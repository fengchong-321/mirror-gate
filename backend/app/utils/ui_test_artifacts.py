"""UI Test Artifacts Manager.

管理 UI 测试生成的截图、视频和日志文件。
"""

import os
import json
import shutil
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path


class UITestArtifactsManager:
    """UI 测试产物管理器。

    负责管理：
    - 截图路径生成
    - 视频录制管理
    - 日志文件管理
    - 旧文件清理
    """

    def __init__(self, base_dir: str = "ui_test_artifacts"):
        """初始化产物管理器。

        Args:
            base_dir: 基础目录
        """
        self.base_dir = base_dir
        self.current_session_dir: Optional[str] = None

    def create_session_dir(self, suite_name: str = "", case_name: str = "") -> str:
        """创建测试会话目录。

        Args:
            suite_name: 套件名称
            case_name: 用例名称

        Returns:
            会话目录路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        dir_name = f"{timestamp}"

        if suite_name:
            dir_name += f"_{self._sanitize_filename(suite_name)}"
        if case_name:
            dir_name += f"_{self._sanitize_filename(case_name)}"

        session_dir = os.path.join(self.base_dir, dir_name)
        os.makedirs(session_dir, exist_ok=True)

        # 创建子目录
        os.makedirs(os.path.join(session_dir, "screenshots"), exist_ok=True)
        os.makedirs(os.path.join(session_dir, "videos"), exist_ok=True)
        os.makedirs(os.path.join(session_dir, "logs"), exist_ok=True)

        self.current_session_dir = session_dir
        return session_dir

    def get_screenshot_path(self, name: str, subdir: str = "") -> str:
        """获取截图保存路径。

        Args:
            name: 文件名
            subdir: 子目录（如 steps）

        Returns:
            截图路径
        """
        if self.current_session_dir:
            base = os.path.join(self.current_session_dir, "screenshots")
        else:
            base = os.path.join(self.base_dir, "screenshots")

        os.makedirs(base, exist_ok=True)

        if subdir:
            subdir_path = os.path.join(base, subdir)
            os.makedirs(subdir_path, exist_ok=True)
            return os.path.join(subdir_path, f"{name}.png")

        return os.path.join(base, f"{name}.png")

    def get_video_path(self, name: str = "recording") -> str:
        """获取视频保存路径。

        Args:
            name: 文件名

        Returns:
            视频路径
        """
        if self.current_session_dir:
            base = os.path.join(self.current_session_dir, "videos")
        else:
            base = os.path.join(self.base_dir, "videos")

        os.makedirs(base, exist_ok=True)
        return os.path.join(base, f"{name}.webm")

    def get_log_path(self, name: str = "execution") -> str:
        """获取日志保存路径。

        Args:
            name: 文件名

        Returns:
            日志路径
        """
        if self.current_session_dir:
            base = os.path.join(self.current_session_dir, "logs")
        else:
            base = os.path.join(self.base_dir, "logs")

        os.makedirs(base, exist_ok=True)
        return os.path.join(base, f"{name}.json")

    def save_execution_log(
        self,
        steps: List[Dict[str, Any]],
        result: Dict[str, Any],
        name: str = "execution",
    ):
        """保存执行日志。

        Args:
            steps: 步骤列表
            result: 执行结果
            name: 日志文件名
        """
        log_path = self.get_log_path(name)

        log_data = {
            "timestamp": datetime.now().isoformat(),
            "steps": steps,
            "result": result,
        }

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)

    def cleanup_old_artifacts(self, days: int = 7):
        """清理旧的产物文件。

        Args:
            days: 保留天数
        """
        if not os.path.exists(self.base_dir):
            return

        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for item in os.listdir(self.base_dir):
            item_path = os.path.join(self.base_dir, item)
            if os.path.isdir(item_path):
                # 从目录名解析时间
                try:
                    # 目录名格式：YYYYMMDD_HHMMSS_xxx
                    date_part = item.split("_")[0]
                    time_part = item.split("_")[1]
                    item_date = datetime.strptime(
                        f"{date_part}_{time_part}", "%Y%m%d_%H%M%S"
                    )

                    if item_date.timestamp() < cutoff_time:
                        shutil.rmtree(item_path)
                        print(f"Cleaned up old artifact: {item}")
                except (IndexError, ValueError):
                    # 无法解析的目录名，跳过
                    pass

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符。

        Args:
            filename: 原始文件名

        Returns:
            清理后的文件名
        """
        # 替换非法字符
        illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        result = filename
        for char in illegal_chars:
            result = result.replace(char, '_')
        # 限制长度
        return result[:50]


# 全局实例
_artifacts_manager: Optional[UITestArtifactsManager] = None


def get_artifacts_manager() -> UITestArtifactsManager:
    """获取全局产物管理器实例。

    Returns:
        UITestArtifactsManager 实例
    """
    global _artifacts_manager
    if _artifacts_manager is None:
        _artifacts_manager = UITestArtifactsManager()
    return _artifacts_manager


def init_artifacts_manager(base_dir: str = "ui_test_artifacts") -> UITestArtifactsManager:
    """初始化产物管理器。

    Args:
        base_dir: 基础目录

    Returns:
        UITestArtifactsManager 实例
    """
    global _artifacts_manager
    _artifacts_manager = UITestArtifactsManager(base_dir)
    return _artifacts_manager
