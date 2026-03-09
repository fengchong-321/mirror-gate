"""UI Test Execution Engine.

This module provides the execution engine for UI tests using:
- Playwright for Web testing
- Airtest + Poco for APP testing
"""

import asyncio
import json
import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


class UIExecutionResult:
    """Result of a UI test step execution."""

    def __init__(self):
        self.success = True
        self.error_message: Optional[str] = None
        self.screenshot_path: Optional[str] = None
        self.duration_ms = 0
        self.details: Dict[str, Any] = {}


class UIExecutor(ABC):
    """Abstract base class for UI test executors."""

    @abstractmethod
    async def setup(self, config: Dict[str, Any]) -> bool:
        """Setup the execution environment."""
        pass

    @abstractmethod
    async def teardown(self):
        """Cleanup after execution."""
        pass

    @abstractmethod
    async def execute_step(self, step: Dict[str, Any]) -> UIExecutionResult:
        """Execute a single test step."""
        pass

    @abstractmethod
    async def take_screenshot(self, name: str) -> Optional[str]:
        """Take a screenshot."""
        pass

    def __init__(self):
        self.browser = None
        self.page = None
        self.context = None
        self.playwright = None
        self.screenshot_dir = "/tmp/screenshots"

    async def setup(self, config: Dict[str, Any]) -> bool:
        """Setup Playwright browser."""
        try:
            from playwright.async_api import async_playwright

            # Create screenshot directory
            os.makedirs(self.screenshot_dir, exist_ok=True)

            # Launch browser
            self.playwright = await async_playwright().start()

            browser_type = config.get("browser", "chromium")
            headless = config.get("headless", True)

            if browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=headless)
            elif browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(headless=headless)
            else:
                self.browser = await self.playwright.chromium.launch(headless=headless)

            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                base_url=config.get("base_url"),
            )

            self.page = await self.context.new_page()

            # Set default timeout
            self.page.set_default_timeout(config.get("timeout", 30000))

            return True

        except ImportError:
            print("Playwright not installed. Install with: pip install playwright && playwright install")
            return False
        except Exception as e:
            print(f"Failed to setup Playwright: {e}")
            return False

    async def teardown(self):
        """Cleanup Playwright resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Error during teardown: {e}")

    async def execute_step(self, step: Dict[str, Any]) -> UIExecutionResult:
        """Execute a test step using Playwright."""
        result = UIExecutionResult()
        start_time = time.time()

        try:
            action = step.get("action")
            params = step.get("params", {})

            if action == "open_url":
                await self.page.goto(params["url"])
                result.details["url"] = params["url"]

            elif action == "click":
                selector = params["selector"]
                await self.page.click(selector)
                result.details["selector"] = selector

            elif action == "input":
                selector = params["selector"]
                text = params["text"]
                await self.page.fill(selector, text)
                result.details["selector"] = selector
                result.details["text"] = text

            elif action == "select":
                selector = params["selector"]
                value = params["value"]
                await self.page.select_option(selector, value)
                result.details["selector"] = selector
                result.details["value"] = value

            elif action == "wait":
                ms = params.get("ms", 1000)
                await self.page.wait_for_timeout(ms)
                result.details["wait_ms"] = ms

            elif action == "wait_for_selector":
                selector = params["selector"]
                timeout = params.get("timeout", 30000)
                await self.page.wait_for_selector(selector, timeout=timeout)
                result.details["selector"] = selector

            elif action == "assert_text":
                selector = params["selector"]
                expected = params["text"]
                actual = await self.page.text_content(selector)
                if expected not in (actual or ""):
                    result.success = False
                    result.error_message = f"Text assertion failed: expected '{expected}' in '{actual}'"
                result.details["expected"] = expected
                result.details["actual"] = actual

            elif action == "assert_visible":
                selector = params["selector"]
                visible = await self.page.is_visible(selector)
                if not visible:
                    result.success = False
                    result.error_message = f"Element not visible: {selector}"
                result.details["selector"] = selector
                result.details["visible"] = visible

            elif action == "screenshot":
                name = params.get("name", f"screenshot_{int(time.time())}")
                path = await self.take_screenshot(name)
                result.screenshot_path = path

            elif action == "scroll":
                selector = params.get("selector")
                if selector:
                    await self.page.locator(selector).scroll_into_view_if_needed()
                else:
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            elif action == "hover":
                selector = params["selector"]
                await self.page.hover(selector)
                result.details["selector"] = selector

            else:
                result.success = False
                result.error_message = f"Unknown action: {action}"

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            # Take screenshot on failure
            try:
                result.screenshot_path = await self.take_screenshot(f"error_{int(time.time())}")
            except:
                pass

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    async def take_screenshot(self, name: str) -> Optional[str]:
        """Take a screenshot."""
        if not self.page:
            return None

        path = os.path.join(self.screenshot_dir, f"{name}.png")
        await self.page.screenshot(path=path)
        return path


class AirtestExecutor(UIExecutor):
    """Airtest + Poco executor for APP UI testing."""

    def __init__(self):
        self.device = None
        self.poco = None
        self.screenshot_dir = "/tmp/screenshots"

    async def setup(self, config: Dict[str, Any]) -> bool:
        """Setup Airtest device connection."""
        try:
            from airtest.core.api import connect_device, snapshot
            from poco.drivers.android.uiautomation import AndroidUiautomationPoco

            # Create screenshot directory
            os.makedirs(self.screenshot_dir, exist_ok=True)

            # Connect to device
            device_uri = config.get("device_uri", "Android:///")
            self.device = connect_device(device_uri)

            # Initialize Poco
            platform = config.get("platform", "android")
            if platform == "android":
                self.poco = AndroidUiautomationPoco()
            elif platform == "ios":
                from poco.drivers.ios import IOSPoco
                self.poco = IOSPoco()
            else:
                # Unity game
                from poco.drivers.unity3d import UnityPoco
                self.poco = UnityPoco()

            return True

        except ImportError:
            print("Airtest/Poco not installed. Install with: pip install airtest pocoui")
            return False
        except Exception as e:
            print(f"Failed to setup Airtest: {e}")
            return False

    async def teardown(self):
        """Cleanup Airtest resources."""
        try:
            if self.device:
                # Airtest doesn't require explicit cleanup
                pass
        except Exception as e:
            print(f"Error during teardown: {e}")

    async def execute_step(self, step: Dict[str, Any]) -> UIExecutionResult:
        """Execute a test step using Airtest/Poco."""
        result = UIExecutionResult()
        start_time = time.time()

        try:
            from airtest.core.api import touch, swipe, text, wait, exists
            from airtest.core.object import Template

            action = step.get("action")
            params = step.get("params", {})

            if action == "tap":
                # Tap by coordinates or template
                if "x" in params and "y" in params:
                    touch((params["x"], params["y"]))
                elif "template" in params:
                    touch(Template(params["template"]))
                elif "element" in params:
                    self.poco(params["element"]).click()

            elif action == "input":
                text_value = params["text"]
                if "element" in params:
                    element = self.poco(params["element"])
                    element.click()
                    text(text_value)
                else:
                    text(text_value)

            elif action == "swipe":
                start = params.get("start", (0.5, 0.8))
                end = params.get("end", (0.5, 0.2))
                swipe(start, end)

            elif action == "wait":
                duration = params.get("seconds", 1)
                wait(duration)

            elif action == "wait_for_element":
                element_name = params["element"]
                timeout = params.get("timeout", 20)
                element = self.poco(element_name)
                element.wait_for_appearance(timeout=timeout)

            elif action == "assert_exists":
                element_name = params["element"]
                if not self.poco(element_name).exists():
                    result.success = False
                    result.error_message = f"Element not found: {element_name}"

            elif action == "assert_text":
                element_name = params["element"]
                expected = params["text"]
                actual = self.poco(element_name).get_text()
                if expected not in (actual or ""):
                    result.success = False
                    result.error_message = f"Text assertion failed: expected '{expected}' in '{actual}'"

            elif action == "screenshot":
                name = params.get("name", f"screenshot_{int(time.time())}")
                path = await self.take_screenshot(name)
                result.screenshot_path = path

            elif action == "start_app":
                package = params["package"]
                self.device.start_app(package)

            elif action == "stop_app":
                package = params["package"]
                self.device.stop_app(package)

            else:
                result.success = False
                result.error_message = f"Unknown action: {action}"

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            # Take screenshot on failure
            try:
                result.screenshot_path = await self.take_screenshot(f"error_{int(time.time())}")
            except:
                pass

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    async def take_screenshot(self, name: str) -> Optional[str]:
        """Take a screenshot."""
        try:
            from airtest.core.api import snapshot

            path = os.path.join(self.screenshot_dir, f"{name}.jpg")
            snapshot(path)
            return path
        except:
            return None


def get_executor(platform: str) -> UIExecutor:
    """Get the appropriate executor for the platform."""
    if platform in ["web", "chromium", "firefox", "webkit"]:
        return PlaywrightExecutor()
    elif platform in ["android", "ios", "app"]:
        return AirtestExecutor()
    else:
        # Default to Playwright for unknown platforms
        return PlaywrightExecutor()


async def execute_ui_test(
    steps: List[Dict[str, Any]],
    platform: str,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute a UI test with the given steps."""
    executor = get_executor(platform)

    results = {
        "success": True,
        "steps": [],
        "total_duration_ms": 0,
        "screenshots": [],
        "error": None,
    }

    try:
        # Setup
        if not await executor.setup(config):
            results["success"] = False
            results["error"] = "Failed to setup executor"
            return results

        # Execute steps
        for idx, step in enumerate(steps):
            step_result = await executor.execute_step(step)

            results["steps"].append({
                "order": idx,
                "action": step.get("action"),
                "success": step_result.success,
                "error": step_result.error_message,
                "duration_ms": step_result.duration_ms,
                "screenshot": step_result.screenshot_path,
            })

            results["total_duration_ms"] += step_result.duration_ms

            if step_result.screenshot_path:
                results["screenshots"].append(step_result.screenshot_path)

            if not step_result.success:
                results["success"] = False
                results["error"] = f"Step {idx} failed: {step_result.error_message}"
                break

    except Exception as e:
        results["success"] = False
        results["error"] = str(e)

    finally:
        await executor.teardown()

    return results
