"""Playwright Executor.

Web UI 自动化执行器，基于 Playwright 实现。
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import os


class PlaywrightExecutor:
    """Playwright Web 执行器。

    使用示例:
        executor = PlaywrightExecutor({"base_url": "https://example.com", "browser": "chromium"})
        result = await executor.execute(steps=[...])
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化执行器。

        Args:
            config: 配置字典
                - base_url: 基础 URL
                - browser: 浏览器类型 (chromium/firefox/webkit)
                - headless: 是否无头模式
                - viewport: 视口大小 {"width": 1920, "height": 1080}
                - slow_mo: 慢动作毫秒数
                - timeout: 默认超时毫秒数
        """
        self.config = config or {}
        self.base_url = self.config.get("base_url", "")
        self.browser_type = self.config.get("browser", "chromium")
        self.headless = self.config.get("headless", True)
        self.viewport = self.config.get("viewport", {"width": 1920, "height": 1080})
        self.slow_mo = self.config.get("slow_mo", 0)
        self.timeout = self.config.get("timeout", 30000)

        self.browser = None
        self.context = None
        self.page = None
        self._execution_context = None

    async def __aenter__(self):
        """异步上下文管理器入口。"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口。"""
        await self.close()

    async def start(self):
        """启动浏览器。"""
        from playwright.async_api import async_playwright

        playwright = await async_playwright().start()

        # 启动浏览器
        browser_launcher = getattr(playwright, self.browser_type)
        self.browser = await browser_launcher.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
        )

        # 创建上下文
        self.context = await self.browser.new_context(
            viewport=self.viewport,
            base_url=self.base_url if self.base_url else None,
        )

        # 创建页面
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout)

        # 创建执行上下文
        self._execution_context = {
            "page": self.page,
            "browser": self.browser,
            "context": self.context,
            "base_url": self.base_url,
        }

    async def close(self):
        """关闭浏览器。"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.page = None
            self.context = None

    async def execute(self, steps: List[Dict[str, Any]], output_dir: str = "screenshots") -> Dict[str, Any]:
        """执行步骤列表。

        Args:
            steps: 步骤列表，每个步骤包含:
                - keyword: Given/When/Then/And
                - text: 步骤描述
                - action: 动作类型
                - params: 动作参数
            output_dir: 输出目录（截图等）

        Returns:
            执行结果字典:
                - success: bool
                - steps: 步骤结果列表
                - total_duration_ms: 总耗时
                - error: 错误信息（如果有）
                - screenshots: 截图路径列表
        """
        from app.services.step_registry import StepRegistry

        start_time = datetime.now()
        results = []
        screenshots = []
        error = None
        success = True

        # 更新执行上下文
        self._execution_context["output_dir"] = output_dir

        for idx, step in enumerate(steps):
            step_start = datetime.now()
            action = step.get("action")
            params = step.get("params", {})

            step_result = {
                "order": idx,
                "keyword": step.get("keyword", "And"),
                "text": step.get("text", ""),
                "action": action,
                "success": True,
                "error": None,
                "duration_ms": 0,
                "screenshot": None,
            }

            try:
                # 获取步骤处理函数
                handler = StepRegistry.get(action, "web")
                if not handler:
                    raise ValueError(f"未注册的步骤类型：{action}")

                # 执行步骤
                result = await handler(self._execution_context, params)

                # 处理截图返回值
                if isinstance(result, dict) and "path" in result:
                    screenshots.append(result["path"])
                    step_result["screenshot"] = result["path"]

            except Exception as e:
                step_result["success"] = False
                step_result["error"] = str(e)
                error = str(e)
                success = False

                # 失败时自动截图
                try:
                    screenshot_path = await self._take_screenshot(
                        output_dir, f"step_{idx}_error"
                    )
                    screenshots.append(screenshot_path)
                    step_result["screenshot"] = screenshot_path
                except Exception:
                    pass

            # 计算步骤耗时
            step_result["duration_ms"] = int((datetime.now() - step_start).total_seconds() * 1000)
            results.append(step_result)

            # 失败时停止执行
            if not success:
                break

        total_duration = int((datetime.now() - start_time).total_seconds() * 1000)

        return {
            "success": success,
            "steps": results,
            "total_duration_ms": total_duration,
            "error": error,
            "screenshots": screenshots,
        }

    async def _take_screenshot(self, output_dir: str, name: str) -> str:
        """截取屏幕。

        Args:
            output_dir: 输出目录
            name: 文件名

        Returns:
            截图路径
        """
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{name}.png")
        await self.page.screenshot(path=path, full_page=True)
        return path

    # ============ 便捷方法 ============

    async def goto(self, url: str, **kwargs):
        """导航到 URL。

        Args:
            url: URL 地址
            **kwargs: 传递给 page.goto() 的参数
        """
        return await self.page.goto(url, **kwargs)

    async def click(self, selector: str, **kwargs):
        """点击元素。

        Args:
            selector: CSS 选择器
            **kwargs: 传递给 page.click() 的参数
        """
        return await self.page.click(selector, **kwargs)

    async def fill(self, selector: str, value: str, **kwargs):
        """输入文本。

        Args:
            selector: CSS 选择器
            value: 要输入的值
            **kwargs: 传递给 page.fill() 的参数
        """
        return await self.page.fill(selector, value, **kwargs)

    async def get_text(self, selector: str) -> str:
        """获取元素文本。

        Args:
            selector: CSS 选择器

        Returns:
            元素文本内容
        """
        locator = self.page.locator(selector)
        return await locator.inner_text()

    async def is_visible(self, selector: str) -> bool:
        """检查元素是否可见。

        Args:
            selector: CSS 选择器

        Returns:
            True 如果元素可见
        """
        locator = self.page.locator(selector)
        return await locator.is_visible()

    async def is_enabled(self, selector: str) -> bool:
        """检查元素是否启用。

        Args:
            selector: CSS 选择器

        Returns:
            True 如果元素启用
        """
        locator = self.page.locator(selector)
        return await locator.is_enabled()

    async def wait_for_selector(self, selector: str, **kwargs):
        """等待元素出现。

        Args:
            selector: CSS 选择器
            **kwargs: 传递给 page.wait_for_selector() 的参数
        """
        return await self.page.wait_for_selector(selector, **kwargs)

    async def expect_text(self, selector: str, expected: str, timeout: int = 5000):
        """等待并断言文本。

        Args:
            selector: CSS 选择器
            expected: 期望的文本
            timeout: 超时毫秒数
        """
        from playwright.async_api import expect

        locator = self.page.locator(selector)
        await expect(locator).to_have_text(expected, timeout=timeout)

    async def expect_visible(self, selector: str, timeout: int = 5000):
        """等待并断言元素可见。

        Args:
            selector: CSS 选择器
            timeout: 超时毫秒数
        """
        from playwright.async_api import expect

        locator = self.page.locator(selector)
        await expect(locator).to_be_visible(timeout=timeout)

    @property
    def url(self) -> str:
        """获取当前 URL。"""
        return self.page.url

    @property
    def title(self) -> str:
        """获取页面标题。"""
        return self.page.title


async def execute_web_test(
    steps: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None,
    output_dir: str = "screenshots",
) -> Dict[str, Any]:
    """执行 Web UI 测试的便捷函数。

    Args:
        steps: 步骤列表
        config: 浏览器配置
        output_dir: 输出目录

    Returns:
        执行结果
    """
    async with PlaywrightExecutor(config) as executor:
        return await executor.execute(steps, output_dir)
