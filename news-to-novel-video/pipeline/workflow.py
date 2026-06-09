"""
LangGraph工作流定义
定义新闻转小说视频的完整流水线
"""
from typing import TypedDict, Annotated
from loguru import logger

from agents.orchestrator import OrchestratorAgent
from config.settings import settings
from models.schemas import PipelineRun


class WorkflowState(TypedDict):
    """工作流状态"""
    pipeline: PipelineRun
    current_step: str
    error: str


class NewsToNovelWorkflow:
    """新闻转小说视频工作流"""

    def __init__(self):
        self.orchestrator = OrchestratorAgent()

    def run(
        self,
        news_count: int = 1,
        style: str = "realism",
        target_length: int = 30000,
        target_scene_count: int = 1800,
        news_index: int = 0,
    ) -> PipelineRun:
        """
        运行完整工作流

        Args:
            news_count: 抓取新闻条数
            style: 小说风格
            target_length: 目标字数
            target_scene_count: 目标分镜数
            news_index: 选择第几条新闻

        Returns:
            PipelineRun 流水线运行记录
        """
        logger.info("工作流启动")

        # 确保目录存在
        settings.ensure_dirs()

        # 执行流水线
        pipeline = self.orchestrator.run(
            news_count=news_count,
            style=style,
            target_length=target_length,
            target_scene_count=target_scene_count,
            news_index=news_index,
        )

        return pipeline

    def run_with_retry(
        self,
        max_retries: int = 3,
        **kwargs,
    ) -> PipelineRun:
        """
        带重试的工作流运行

        Args:
            max_retries: 最大重试次数
            **kwargs: 传递给run的参数

        Returns:
            PipelineRun 流水线运行记录
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.info(f"工作流尝试 {attempt + 1}/{max_retries}")
                pipeline = self.run(**kwargs)
                return pipeline
            except Exception as e:
                last_error = e
                logger.error(f"工作流失败 (尝试 {attempt + 1}/{max_retries}): {e}")

        raise RuntimeError(f"工作流在{max_retries}次尝试后仍然失败: {last_error}")