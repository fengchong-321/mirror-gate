"""Variable resolver for API testing.

This module provides variable resolution and substitution for test parameterization.
"""

import json
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.orm import Session

from app.models.api_test import ApiTestVariable, ApiTestSuite


# Pattern for variable substitution: ${variable_name}
VARIABLE_PATTERN = re.compile(r'\$\{([^}]+)\}')


class VariableResolver:
    """Resolves variables in test configurations."""

    # Built-in variable generators
    BUILTIN_VARS = {
        'timestamp': lambda: str(int(datetime.now().timestamp() * 1000)),
        'timestamp_sec': lambda: str(int(datetime.now().timestamp())),
        'date': lambda: datetime.now().strftime('%Y-%m-%d'),
        'datetime': lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'iso_datetime': lambda: datetime.now().isoformat(),
        'uuid': lambda: str(uuid.uuid4()),
        'uuid_hex': lambda: uuid.uuid4().hex,
        'random_int': lambda: str(uuid.uuid4().int & (10**9 - 1)),
        'random_16': lambda: str(uuid.uuid4().int & (16**10 - 1)),
    }

    def __init__(self, db: Optional[Session] = None, suite_id: Optional[int] = None):
        """Initialize variable resolver.

        Args:
            db: Database session for loading stored variables
            suite_id: Suite ID to load variables for
        """
        self.db = db
        self.suite_id = suite_id
        self._variables: Dict[str, Any] = {}
        self._dynamic_vars: Dict[str, Any] = {}

        # Load stored variables if db and suite_id provided
        if db and suite_id:
            self._load_stored_variables()

    def _load_stored_variables(self):
        """Load variables from database."""
        if not self.db:
            return

        variables = self.db.query(ApiTestVariable).filter(
            ApiTestVariable.suite_id == self.suite_id
        ).all()

        for var in variables:
            value = self._convert_value(var.value, var.type)
            self._variables[var.name] = value

    def _convert_value(self, value: str, var_type: str) -> Any:
        """Convert string value to appropriate type."""
        if var_type == 'number':
            try:
                return int(value)
            except ValueError:
                try:
                    return float(value)
                except ValueError:
                    return value
        elif var_type == 'boolean':
            return value.lower() in ('true', '1', 'yes')
        elif var_type == 'json':
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        else:  # string
            return value

    def set_variable(self, name: str, value: Any):
        """Set a variable value (can be used for dynamic variables)."""
        self._dynamic_vars[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable value."""
        # Check dynamic vars first
        if name in self._dynamic_vars:
            return self._dynamic_vars[name]
        # Then check stored vars
        if name in self._variables:
            return self._variables[name]
        # Then check built-in vars
        if name in self.BUILTIN_VARS:
            return self.BUILTIN_VARS[name]()
        return default

    def resolve(self, text: Union[str, Dict, List, Any]) -> Union[str, Dict, List, Any]:
        """Resolve all variables in text or structure.

        Args:
            text: String, dict, or list to resolve variables in

        Returns:
            Same type with all ${variable} patterns replaced
        """
        if text is None:
            return None

        if isinstance(text, str):
            return self._resolve_string(text)
        elif isinstance(text, dict):
            return {k: self.resolve(v) for k, v in text.items()}
        elif isinstance(text, list):
            return [self.resolve(item) for item in text]
        else:
            return text

    def _resolve_string(self, text: str) -> str:
        """Resolve variables in a string."""
        def replace_var(match):
            var_name = match.group(1)

            # Check for built-in variable generators
            if var_name in self.BUILTIN_VARS:
                return self.BUILTIN_VARS[var_name]()

            # Check dynamic variables
            if var_name in self._dynamic_vars:
                value = self._dynamic_vars[var_name]
                return str(value) if value is not None else ''

            # Check stored variables
            if var_name in self._variables:
                value = self._variables[var_name]
                return str(value) if value is not None else ''

            # Return original if not found
            return match.group(0)

        return VARIABLE_PATTERN.sub(replace_var, text)

    def extract_json_path_to_var(
        self,
        var_name: str,
        json_data: Union[str, Dict, List],
        json_path: str,
    ) -> bool:
        """Extract value from JSON and store as variable.

        Args:
            var_name: Name to store the extracted value
            json_data: JSON data to extract from
            json_path: JSONPath expression

        Returns:
            True if extraction succeeded
        """
        try:
            from app.utils.jsonpath_utils import extract_first
            value = extract_first(json_data, json_path)
            if value is not None:
                self.set_variable(var_name, value)
                return True
            return False
        except Exception:
            return False

    def clear_dynamic(self):
        """Clear dynamic variables (keeps stored variables)."""
        self._dynamic_vars.clear()

    def get_all_variables(self) -> Dict[str, Any]:
        """Get all variables (stored + dynamic + built-in snapshot)."""
        all_vars = dict(self._variables)
        all_vars.update(self._dynamic_vars)
        return all_vars


class ScriptExecutor:
    """Executes pre/post scripts for test cases."""

    def __init__(self, variable_resolver: VariableResolver):
        """Initialize script executor.

        Args:
            variable_resolver: VariableResolver instance for variable access
        """
        self.variable_resolver = variable_resolver

    def execute_script(self, script: str) -> bool:
        """Execute a Python script with variable resolver access.

        Args:
            script: Python script code to execute

        Returns:
            True if execution succeeded

        Security Note: This uses exec() which can be dangerous. In production,
        consider using a sandboxed environment or restricted execution.
        """
        if not script or not script.strip():
            return True

        try:
            # Create execution context with variable resolver
            context = {
                'vars': self.variable_resolver,
                'set_var': self.variable_resolver.set_variable,
                'get_var': self.variable_resolver.get_variable,
                'print': print,
                'json': json,
                'datetime': datetime,
                'uuid': uuid,
            }

            # Execute the script
            exec(script, {}, context)
            return True

        except Exception as e:
            # Log error but don't expose internals
            return False
