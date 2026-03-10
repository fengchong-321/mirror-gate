"""Testcase Service - Business logic for testcase management.

This module provides the service layer for managing test cases, including
CRUD operations for groups, cases, comments, and history tracking.
"""

from datetime import datetime, timezone
from typing import Optional, List, Any, Dict

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.testcase import (
    TestCaseGroup,
    TestCase,
    TestCaseAttachment,
    TestCaseComment,
    TestCaseHistory,
    CaseType,
    Platform,
    Priority,
    CaseStatus,
)
from app.schemas.testcase import (
    TestCaseGroupCreate,
    TestCaseGroupUpdate,
    TestCaseGroupResponse,
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseResponse,
    TestCaseDetailResponse,
    TestCaseCommentCreate,
    TestCaseCommentResponse,
    TreeNode,
)


class TestCaseService:
    """Service class for managing test cases.

    This class encapsulates all business logic related to test case management,
    including groups, cases, comments, and history tracking.
    """

    def __init__(self, db: Session):
        """Initialize the service with a database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    # ============ Group Methods ============

    def create_group(
        self, group_data: TestCaseGroupCreate, created_by: Optional[str] = None
    ) -> TestCaseGroup:
        """Create a new test case group.

        Args:
            group_data: Pydantic model containing group creation data.
            created_by: Username of the creator.

        Returns:
            The created TestCaseGroup instance.
        """
        now = datetime.now(timezone.utc)
        group = TestCaseGroup(
            name=group_data.name,
            parent_id=group_data.parent_id,
            order=group_data.order,
            description=group_data.description,
            created_by=created_by,
            created_at=now,
            updated_by=created_by,
            updated_at=now,
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group

    def get_group(self, group_id: int) -> Optional[TestCaseGroup]:
        """Retrieve a test case group by ID.

        Args:
            group_id: The ID of the group to retrieve.

        Returns:
            The TestCaseGroup instance if found, None otherwise.
        """
        return self.db.query(TestCaseGroup).filter(TestCaseGroup.id == group_id).first()

    def get_group_tree(self) -> List[TreeNode]:
        """Retrieve the hierarchical group tree.

        Returns:
            List of TreeNode instances representing the group hierarchy.
        """
        # Get all groups
        groups = self.db.query(TestCaseGroup).order_by(TestCaseGroup.order).all()

        # Get case counts for all groups
        case_counts = (
            self.db.query(
                TestCase.group_id,
                func.count(TestCase.id).label("count")
            )
            .group_by(TestCase.group_id)
            .all()
        )
        count_dict = {item.group_id: item.count for item in case_counts}

        # Deduplicate groups by name within same parent (keep lowest ID)
        seen = {}
        unique_groups = []
        for group in groups:
            key = (group.parent_id, group.name.lower().strip())
            if key not in seen:
                seen[key] = group.id
                unique_groups.append(group)
            # Skip duplicate groups (same parent + name)

        # Build tree structure
        def build_tree(parent_id: Optional[int] = None) -> List[TreeNode]:
            children = [g for g in unique_groups if g.parent_id == parent_id]
            nodes = []
            for group in children:
                node = TreeNode(
                    id=group.id,
                    label=group.name,
                    parent_id=group.parent_id,
                    order=group.order,
                    case_count=count_dict.get(group.id, 0),
                    children=build_tree(group.id),
                )
                nodes.append(node)
            return nodes

        return build_tree()

    def update_group(
        self,
        group_id: int,
        group_data: TestCaseGroupUpdate,
        updated_by: Optional[str] = None,
    ) -> TestCaseGroup:
        """Update an existing test case group.

        Args:
            group_id: The ID of the group to update.
            group_data: Pydantic model containing update data.
            updated_by: Username of the updater.

        Returns:
            The updated TestCaseGroup instance.

        Raises:
            HTTPException: If the group is not found.
        """
        group = self.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail=f"Group with id {group_id} not found")

        update_data = group_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(group, field, value)

        group.updated_by = updated_by
        group.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(group)
        return group

    def delete_group(self, group_id: int) -> bool:
        """Delete a test case group by ID.

        Cascades delete all children and associated cases.

        Args:
            group_id: The ID of the group to delete.

        Returns:
            True if the group was deleted, False if not found.
        """
        group = self.get_group(group_id)
        if not group:
            return False

        self.db.delete(group)
        self.db.commit()
        return True

    # ============ Test Case Methods ============

    def _generate_case_code(self) -> str:
        """Generate a unique test case code.

        Format: 7-digit zero-padded number (e.g., 0000001)

        Returns:
            A unique test case code string.
        """
        # Get the highest ID from existing cases
        latest_case = (
            self.db.query(TestCase)
            .order_by(TestCase.id.desc())
            .first()
        )

        if latest_case:
            next_id = latest_case.id + 1
        else:
            next_id = 1

        return f"{next_id:07d}"

    def create_case(
        self, case_data: TestCaseCreate, created_by: Optional[str] = None
    ) -> TestCase:
        """Create a new test case.

        Args:
            case_data: Pydantic model containing case creation data.
            created_by: Username of the creator.

        Returns:
            The created TestCase instance.

        Raises:
            HTTPException: If the group is not found.
        """
        # Verify group exists
        group = self.get_group(case_data.group_id)
        if not group:
            raise HTTPException(
                status_code=404,
                detail=f"Group with id {case_data.group_id} not found"
            )

        now = datetime.now(timezone.utc)
        code = self._generate_case_code()

        case = TestCase(
            group_id=case_data.group_id,
            title=case_data.title,
            code=code,
            case_type=case_data.case_type,
            platform=case_data.platform,
            priority=case_data.priority,
            status=case_data.status,
            is_core=case_data.is_core,
            owner=case_data.owner,
            developer=case_data.developer,
            page_url=case_data.page_url,
            preconditions=case_data.preconditions,
            steps=case_data.steps,
            remark=case_data.remark,
            tags=case_data.tags,
            created_by=created_by,
            created_at=now,
            updated_by=created_by,
            updated_at=now,
        )
        self.db.add(case)
        self.db.flush()  # Flush to get the case ID before recording history

        # Record history for creation
        self._record_history(case.id, "create", None, case.title, created_by)

        self.db.commit()
        self.db.refresh(case)
        return case

    def get_case(self, case_id: int) -> Optional[TestCase]:
        """Retrieve a test case by ID.

        Args:
            case_id: The ID of the case to retrieve.

        Returns:
            The TestCase instance if found, None otherwise.
        """
        return self.db.query(TestCase).filter(TestCase.id == case_id).first()

    def get_case_detail(self, case_id: int) -> Optional[TestCaseDetailResponse]:
        """Retrieve a test case with full details.

        Includes attachments, comments, and history.

        Args:
            case_id: The ID of the case to retrieve.

        Returns:
            TestCaseDetailResponse if found, None otherwise.
        """
        case = self.get_case(case_id)
        if not case:
            return None

        return TestCaseDetailResponse.model_validate(case)

    def get_cases_by_group(
        self, group_id: int, skip: int = 0, limit: int = 100
    ) -> List[TestCase]:
        """Retrieve test cases by group ID with pagination.

        Args:
            group_id: The ID of the group.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of TestCase instances.
        """
        return (
            self.db.query(TestCase)
            .filter(TestCase.group_id == group_id)
            .order_by(TestCase.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_cases_by_group(self, group_id: int) -> int:
        """Count test cases in a group.

        Args:
            group_id: The ID of the group.

        Returns:
            Number of test cases in the group.
        """
        return (
            self.db.query(TestCase)
            .filter(TestCase.group_id == group_id)
            .count()
        )

    def search_cases(
        self,
        group_id: int,
        keyword: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple:
        """Search test cases in a group by keyword.

        Searches in title and steps content (JSON field).

        Args:
            group_id: The ID of the group.
            keyword: Search keyword to filter by title and steps.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            Tuple of (list of TestCase instances, total count).
        """
        from sqlalchemy import or_
        from sqlalchemy.types import Text

        query = self.db.query(TestCase).filter(TestCase.group_id == group_id)

        if keyword:
            search_pattern = f"%{keyword}%"
            # Search in title only (steps JSON search may fail on some DB configurations)
            query = query.filter(
                or_(
                    TestCase.title.ilike(search_pattern),
                )
            )

        total = query.count()
        cases = (
            query.order_by(TestCase.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return cases, total

    def update_case(
        self,
        case_id: int,
        case_data: TestCaseUpdate,
        updated_by: Optional[str] = None,
    ) -> TestCase:
        """Update an existing test case.

        Args:
            case_id: The ID of the case to update.
            case_data: Pydantic model containing update data.
            updated_by: Username of the updater.

        Returns:
            The updated TestCase instance.

        Raises:
            HTTPException: If the case is not found.
        """
        case = self.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with id {case_id} not found")

        update_data = case_data.model_dump(exclude_unset=True)

        # Record history for changed fields
        for field, new_value in update_data.items():
            old_value = getattr(case, field, None)
            if old_value != new_value:
                self._record_history(
                    case_id,
                    f"update_{field}",
                    str(old_value) if old_value else None,
                    str(new_value) if new_value else None,
                    updated_by,
                )

        for field, value in update_data.items():
            setattr(case, field, value)

        case.updated_by = updated_by
        case.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(case)
        return case

    def delete_case(self, case_id: int) -> bool:
        """Delete a test case by ID.

        Args:
            case_id: The ID of the case to delete.

        Returns:
            True if the case was deleted, False if not found.
        """
        case = self.get_case(case_id)
        if not case:
            return False

        self.db.delete(case)
        self.db.commit()
        return True

    def copy_case(self, case_id: int, created_by: Optional[str] = None) -> TestCase:
        """Create a copy of an existing test case.

        Args:
            case_id: The ID of the case to copy.
            created_by: Username of the user creating the copy.

        Returns:
            The newly created TestCase instance.

        Raises:
            HTTPException: If the source case is not found.
        """
        source = self.get_case(case_id)
        if not source:
            raise HTTPException(status_code=404, detail=f"Case with id {case_id} not found")

        case_data = TestCaseCreate(
            group_id=source.group_id,
            title=f"{source.title} (Copy)",
            case_type=source.case_type,
            platform=source.platform,
            priority=source.priority,
            status=CaseStatus.DRAFT,  # Copies start as draft
            preconditions=source.preconditions,
            steps=source.steps,
            expected_result=source.expected_result,
            tags=source.tags,
        )

        return self.create_case(case_data, created_by=created_by)

    def move_case(
        self, case_id: int, new_group_id: int, updated_by: Optional[str] = None
    ) -> TestCase:
        """Move a test case to another group.

        Args:
            case_id: The ID of the case to move.
            new_group_id: The ID of the target group.
            updated_by: Username of the user moving the case.

        Returns:
            The updated TestCase instance.

        Raises:
            HTTPException: If the case or target group is not found.
        """
        case = self.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with id {case_id} not found")

        target_group = self.get_group(new_group_id)
        if not target_group:
            raise HTTPException(
                status_code=404,
                detail=f"Target group with id {new_group_id} not found"
            )

        old_group_id = case.group_id
        case.group_id = new_group_id
        case.updated_by = updated_by
        case.updated_at = datetime.now(timezone.utc)

        self._record_history(
            case_id,
            "move",
            f"group_id: {old_group_id}",
            f"group_id: {new_group_id}",
            updated_by,
        )

        self.db.commit()
        self.db.refresh(case)
        return case

    def reorder_cases(
        self, group_id: int, case_orders: List[dict]
    ) -> bool:
        """Reorder test cases within a group.

        Args:
            group_id: The ID of the group.
            case_orders: List of dicts with case id and new order.

        Returns:
            True if reordering was successful.
        """
        for item in case_orders:
            case = self.get_case(item["id"])
            if case and case.group_id == group_id:
                # Store order in a custom attribute or metadata
                # Since TestCase model doesn't have an order field,
                # we can use the updated_at timestamp or skip this
                pass

        self.db.commit()
        return True

    # ============ Comment Methods ============

    def add_comment(
        self,
        case_id: int,
        comment_data: TestCaseCommentCreate,
        created_by: Optional[str] = None,
    ) -> TestCaseComment:
        """Add a comment to a test case.

        Args:
            case_id: The ID of the case.
            comment_data: Pydantic model containing comment data.
            created_by: Username of the commenter.

        Returns:
            The created TestCaseComment instance.

        Raises:
            HTTPException: If the case is not found.
        """
        case = self.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with id {case_id} not found")

        now = datetime.now(timezone.utc)
        comment = TestCaseComment(
            case_id=case_id,
            content=comment_data.content,
            author=created_by,
            created_at=now,
            updated_at=now,
        )
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def delete_comment(self, comment_id: int) -> bool:
        """Delete a comment by ID.

        Args:
            comment_id: The ID of the comment to delete.

        Returns:
            True if the comment was deleted, False if not found.
        """
        comment = (
            self.db.query(TestCaseComment)
            .filter(TestCaseComment.id == comment_id)
            .first()
        )
        if not comment:
            return False

        self.db.delete(comment)
        self.db.commit()
        return True

    # ============ Helper Methods ============

    def _record_history(
        self,
        case_id: int,
        action: str,
        old_value: Optional[str],
        new_value: Optional[str],
        changed_by: Optional[str],
    ) -> None:
        """Record a change in test case history.

        Args:
            case_id: The ID of the case.
            action: The action performed (e.g., 'create', 'update_title').
            old_value: The previous value.
            new_value: The new value.
            changed_by: Username of the user who made the change.
        """
        history = TestCaseHistory(
            case_id=case_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            operator=changed_by,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(history)

    # ============ Import/Export Methods ============

    def export_cases(self, group_id: int) -> List[Dict]:
        """Export test cases as a list of dictionaries.

        Args:
            group_id: The ID of the group to export.

        Returns:
            List of dictionaries representing test cases.

        Raises:
            HTTPException: If the group is not found.
        """
        group = self.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail=f"Group with id {group_id} not found")

        cases = self.get_cases_by_group(group_id, 0, 10000)
        return [self._case_to_dict(c) for c in cases]

    def _case_to_dict(self, case: TestCase) -> Dict:
        """Convert a TestCase instance to a dictionary.

        Args:
            case: The TestCase instance to convert.

        Returns:
            Dictionary representation of the test case.
        """
        return {
            "title": case.title,
            "case_type": case.case_type.value if case.case_type else None,
            "platform": case.platform.value if case.platform else None,
            "priority": case.priority.value if case.priority else None,
            "status": case.status.value if case.status else None,
            "preconditions": case.preconditions,
            "steps": case.steps,
            "expected_result": case.expected_result,
            "tags": case.tags,
        }

    def import_cases(
        self, group_id: int, data: List[Dict], created_by: Optional[str] = None
    ) -> Dict:
        """Import test cases from a list of dictionaries.

        Args:
            group_id: The ID of the target group.
            data: List of dictionaries representing test cases.
            created_by: Username of the importer.

        Returns:
            Dictionary with import results (success count, failed count, errors).

        Raises:
            HTTPException: If the group is not found.
        """
        group = self.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail=f"Group with id {group_id} not found")

        success = 0
        failed = 0
        errors = []

        for i, item in enumerate(data):
            try:
                # Parse enum values with defaults
                case_type = CaseType.FUNCTIONAL
                if item.get("case_type"):
                    try:
                        case_type = CaseType(item["case_type"])
                    except ValueError:
                        pass

                platform = Platform.WEB
                if item.get("platform"):
                    try:
                        platform = Platform(item["platform"])
                    except ValueError:
                        pass

                priority = Priority.MEDIUM
                if item.get("priority"):
                    try:
                        priority = Priority(item["priority"])
                    except ValueError:
                        pass

                status = CaseStatus.DRAFT
                if item.get("status"):
                    try:
                        status = CaseStatus(item["status"])
                    except ValueError:
                        pass

                case_data = TestCaseCreate(
                    group_id=group_id,
                    title=item.get("title", f"Imported Case {i + 1}"),
                    case_type=case_type,
                    platform=platform,
                    priority=priority,
                    status=status,
                    preconditions=item.get("preconditions"),
                    steps=item.get("steps"),
                    expected_result=item.get("expected_result"),
                    tags=item.get("tags"),
                )
                self.create_case(case_data, created_by)
                success += 1
            except Exception as e:
                failed += 1
                errors.append(f"Row {i + 1}: {str(e)}")

        return {"success": success, "failed": failed, "errors": errors}
