"""
Processor Agent（处理智能体）
负责脱敏 + 小说化改写 + 分镜脚本生成
"""
from loguru import logger

from skills.remove_pii import remove_pii
from skills.rewrite_novel import rewrite_as_novel
from skills.split_scenes import split_into_scenes
from models.schemas import RawNews, SanitizedNews, NovelDraft, Scene


class ProcessorAgent:
    """处理智能体：编剧"""

    def __init__(self):
        self.name = "ProcessorAgent"

    def run(
        self,
        news: RawNews,
        style: str = "realism",
        target_length: int = 30000,
        target_scene_count: int = 1800,
    ) -> tuple[SanitizedNews, NovelDraft, list[Scene]]:
        """
        执行完整处理流程：脱敏 → 改写 → 分镜

        Args:
            news: 原始新闻
            style: 小说风格
            target_length: 目标字数
            target_scene_count: 目标分镜数

        Returns:
            (脱敏后新闻, 小说稿, 分镜列表)
        """
        logger.info(f"[{self.name}] 开始处理新闻: {news.title[:30]}...")

        # 步骤1: PII脱敏
        logger.info(f"[{self.name}] 步骤1: PII脱敏")
        sanitized = remove_pii(text=news.content)
        sanitized.original_news_id = news.id

        # 检查脱敏置信度
        if sanitized.confidence_score < 0.5:
            logger.warning(f"[{self.name}] 脱敏置信度较低: {sanitized.confidence_score:.2f}，建议人工复查")

        # 步骤2: 小说化改写
        logger.info(f"[{self.name}] 步骤2: 小说化改写")
        novel = rewrite_as_novel(
            text=sanitized.sanitized_content,
            style=style,
            target_length=target_length,
        )
        novel.sanitized_news_id = sanitized.id

        # 步骤3: 分镜脚本生成
        logger.info(f"[{self.name}] 步骤3: 分镜脚本生成")
        scenes = split_into_scenes(
            novel_text=novel.full_text,
            target_scene_count=target_scene_count,
        )

        # 更新分镜的novel_id
        for scene in scenes:
            scene.novel_id = novel.id

        logger.info(
            f"[{self.name}] 处理完成: 脱敏置信度{sanitized.confidence_score:.2f}, "
            f"小说{novel.word_count}字, {len(scenes)}个分镜"
        )

        return sanitized, novel, scenes