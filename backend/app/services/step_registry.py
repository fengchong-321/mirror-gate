"""UI Test Step Registry.

步骤注册表模块，用于管理 UI 测试步骤的执行函数。
支持按平台（web/app）注册和获取步骤处理函数。
"""

from typing import Callable, Dict, Optional, Any
from functools import wraps


class StepRegistry:
    """UI 测试步骤注册表（单例模式）。

    使用示例:
        # 注册步骤
        @StepRegistry.register("open_url", "web")
        async def open_url_web(page, params):
            await page.goto(params["url"])

        # 获取步骤处理函数
        handler = StepRegistry.get("open_url", "web")
    """

    _registry: Dict[str, Dict[str, Callable]] = {}
    _metadata: Dict[str, Dict[str, Dict[str, Any]]] = {}

    @classmethod
    def register(cls, action: str, platform: str, description: str = ""):
        """注册步骤处理函数的装饰器。

        Args:
            action: 动作名称（如：open_url, click, input）
            platform: 平台名称（web/app）
            description: 步骤描述

        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            # 注册函数
            if action not in cls._registry:
                cls._registry[action] = {}
            cls._registry[action][platform] = func

            # 注册元数据
            if action not in cls._metadata:
                cls._metadata[action] = {}
            cls._metadata[action][platform] = {
                "description": description,
                "func_name": func.__name__,
            }

            return func
        return decorator

    @classmethod
    def get(cls, action: str, platform: str) -> Optional[Callable]:
        """获取步骤处理函数。

        Args:
            action: 动作名称
            platform: 平台名称

        Returns:
            步骤处理函数，如果不存在则返回 None
        """
        return cls._registry.get(action, {}).get(platform)

    @classmethod
    def has_action(cls, action: str, platform: str) -> bool:
        """检查动作是否已注册。

        Args:
            action: 动作名称
            platform: 平台名称

        Returns:
            True 如果动作已注册
        """
        return action in cls._registry and platform in cls._registry.get(action, {})

    @classmethod
    def get_actions(cls, platform: Optional[str] = None) -> list:
        """获取所有已注册的动作列表。

        Args:
            platform: 可选的平台过滤

        Returns:
            动作名称列表
        """
        if platform:
            actions = []
            for action, platforms in cls._registry.items():
                if platform in platforms:
                    actions.append(action)
            return actions
        return list(cls._registry.keys())

    @classmethod
    def get_metadata(cls, action: str, platform: str) -> Optional[Dict[str, Any]]:
        """获取步骤的元数据。

        Args:
            action: 动作名称
            platform: 平台名称

        Returns:
            元数据字典
        """
        return cls._metadata.get(action, {}).get(platform)

    @classmethod
    def get_all_metadata(cls, platform: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """获取所有步骤的元数据。

        Args:
            platform: 可选的平台过滤

        Returns:
            元数据字典 {action: {platform: metadata}}
        """
        result = {}
        for action, platforms in cls._registry.items():
            if platform and platform not in platforms:
                continue
            result[action] = {}
            for plat, metadata in cls._metadata.get(action, {}).items():
                if platform is None or plat == platform:
                    result[action][plat] = metadata
        return result

    @classmethod
    def clear(cls):
        """清空注册表（主要用于测试）。"""
        cls._registry.clear()
        cls._metadata.clear()


# ============ Web 步骤注册 ============

@StepRegistry.register("open_url", "web", "打开 URL 地址")
async def open_url_web(context: Any, params: Dict[str, Any]) -> bool:
    """打开 URL（Web - Playwright）。

    Args:
        context: Playwright page 对象
        params: {"url": str, "wait_until": str (可选)}
    """
    url = params.get("url", "")
    wait_until = params.get("wait_until", "domcontentloaded")

    # 如果是相对 URL，拼接 base_url
    if url.startswith("/") and context.get("base_url"):
        url = context["base_url"] + url

    await context["page"].goto(url, wait_until=wait_until)
    return True


@StepRegistry.register("click", "web", "点击元素")
async def click_web(context: Any, params: Dict[str, Any]) -> bool:
    """点击元素（Web - Playwright）。

    Args:
        context: Playwright page 对象
        params: {"selector": str, "timeout": int (可选)}
    """
    selector = params.get("selector", "")
    timeout = params.get("timeout", 5000)

    await context["page"].click(selector, timeout=timeout)
    return True


@StepRegistry.register("input", "web", "输入文本")
async def input_web(context: Any, params: Dict[str, Any]) -> bool:
    """输入文本（Web - Playwright）。

    Args:
        context: Playwright page 对象
        params: {"selector": str, "value": str, "delay": int (可选)}
    """
    selector = params.get("selector", "")
    value = params.get("value", "")
    delay = params.get("delay", 50)

    await context["page"].fill(selector, value, delay=delay)
    return True


@StepRegistry.register("press_key", "web", "按下键盘")
async def press_key_web(context: Any, params: Dict[str, Any]) -> bool:
    """按下键盘（Web - Playwright）。

    Args:
        context: Playwright page 对象
        params: {"key": str} 如 "Enter", "Tab", "Escape"
    """
    key = params.get("key", "")
    await context["page"].keyboard.press(key)
    return True


@StepRegistry.register("assert_element", "web", "断言元素存在/可见")
async def assert_element_web(context: Any, params: Dict[str, Any]) -> bool:
    """断言元素（Web - Playwright）。

    Args:
        context: Playwright page 对象
        params: {"selector": str, "expected": "visible|hidden|exists", "timeout": int}
    """
    selector = params.get("selector", "")
    expected = params.get("expected", "visible")
    timeout = params.get("timeout", 5000)

    if expected == "hidden":
        await context["page"].wait_for_selector(selector, state="hidden", timeout=timeout)
    elif expected == "exists":
        await context["page"].wait_for_selector(selector, timeout=timeout)
    else:  # visible
        await context["page"].wait_for_selector(selector, state="visible", timeout=timeout)

    return True


@StepRegistry.register("assert_text", "web", "断言文本内容")
async def assert_text_web(context: Any, params: Dict[str, Any]) -> bool:
    """断言文本内容（Web - Playwright）。

    Args:
        context: Playwright page 对象
        params: {"selector": str, "text": str, "contains": bool (可选)}
    """
    selector = params.get("selector", "")
    expected_text = params.get("text", "")
    contains = params.get("contains", False)

    if contains:
        await context["page"].expect_selector(selector, to_have_text=expected_text)
    else:
        locator = context["page"].locator(selector)
        actual_text = await locator.inner_text()
        if expected_text not in actual_text:
            raise AssertionError(f"Expected '{expected_text}' in '{actual_text}'")

    return True


@StepRegistry.register("assert_url", "web", "断言当前 URL")
async def assert_url_web(context: Any, params: Dict[str, Any]) -> bool:
    """断言当前 URL（Web - Playwright）。

    Args:
        context: Playwright page 对象
        params: {"url": str, "contains": bool (可选)}
    """
    expected_url = params.get("url", "")
    contains = params.get("contains", False)

    current_url = context["page"].url

    if contains:
        if expected_url not in current_url:
            raise AssertionError(f"Expected '{expected_url}' in '{current_url}'")
    else:
        if current_url != expected_url:
            raise AssertionError(f"Expected URL '{expected_url}', got '{current_url}'")

    return True


@StepRegistry.register("screenshot", "web", "截图")
async def screenshot_web(context: Any, params: Dict[str, Any]) -> Dict[str, str]:
    """截图（Web - Playwright）。

    Args:
        context: Playwright page 对象
        params: {"name": str (可选), "full_page": bool (可选)}

    Returns:
        {"path": str} 截图路径
    """
    import os
    from datetime import datetime

    name = params.get("name", f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    full_page = params.get("full_page", True)
    output_dir = context.get("output_dir", "screenshots")

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{name}.png")

    await context["page"].screenshot(path=path, full_page=full_page)

    return {"path": path}


@StepRegistry.register("wait", "web", "等待")
async def wait_web(context: Any, params: Dict[str, Any]) -> bool:
    """等待（Web - Playwright）。

    Args:
        context: Playwright page 对象
        params: {"ms": int} 毫秒数
    """
    import asyncio
    ms = params.get("ms", 1000)
    await asyncio.sleep(ms / 1000)
    return True


@StepRegistry.register("hover", "web", "悬停")
async def hover_web(context: Any, params: Dict[str, Any]) -> bool:
    """悬停在元素上（Web - Playwright）。

    Args:
        context: Playwright page 对象
        params: {"selector": str}
    """
    selector = params.get("selector", "")
    await context["page"].hover(selector)
    return True


@StepRegistry.register("select", "web", "选择下拉选项")
async def select_web(context: Any, params: Dict[str, Any]) -> bool:
    """选择下拉选项（Web - Playwright）。

    Args:
        context: Playwright page 对象
        params: {"selector": str, "value": str or list}
    """
    selector = params.get("selector", "")
    value = params.get("value", "")
    await context["page"].select_option(selector, value)
    return True


@StepRegistry.register("scroll", "web", "滚动")
async def scroll_web(context: Any, params: Dict[str, Any]) -> bool:
    """滚动页面（Web - Playwright）。

    Args:
        context: Playwright page 对象
        params: {"x": int (可选), "y": int (可选)}
    """
    x = params.get("x", 0)
    y = params.get("y", 0)
    await context["page"].evaluate(f"window.scrollTo({x}, {y})")
    return True


# ============ App 步骤占位 ============
# 实际实现需要 Airtest/Poco

@StepRegistry.register("open_app", "app", "打开 App")
async def open_app_app(context: Any, params: Dict[str, Any]) -> bool:
    """打开 App（App - Airtest）。

    注：需要安装 airtest 和 poco 库

    Args:
        context: 执行上下文
        params: {"package": str} App 包名
    """
    # TODO: 实现 Airtest 的 open_app
    print(f"TODO: 实现 Airtest open_app: {params.get('package')}")
    return True


@StepRegistry.register("touch", "app", "触摸点击")
async def touch_app(context: Any, params: Dict[str, Any]) -> bool:
    """触摸点击（App - Airtest）。

    Args:
        context: 执行上下文
        params: {"x": int, "y": int} 或 {"selector": str}
    """
    # TODO: 实现 Airtest 的 touch
    print(f"TODO: 实现 Airtest touch: {params}")
    return True


# 初始化 Web 平台的步骤注册
WEB_STEPS = [
    ("open_url", "打开 URL 地址"),
    ("click", "点击元素"),
    ("input", "输入文本"),
    ("press_key", "按下键盘"),
    ("assert_element", "断言元素存在/可见"),
    ("assert_text", "断言文本内容"),
    ("assert_url", "断言当前 URL"),
    ("screenshot", "截图"),
    ("wait", "等待"),
    ("hover", "悬停"),
    ("select", "选择下拉选项"),
    ("scroll", "滚动"),
]

APP_STEPS = [
    ("open_app", "打开 App"),
    ("touch", "触摸点击"),
    # 更多 App 步骤待实现
]
