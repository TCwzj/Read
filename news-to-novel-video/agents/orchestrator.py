"""
Orchestrator Agent（编排智能体）
负责整体流程调度、异常处理、质量把控
"""
from datetime import datetime
from loguru import logger

from agents.scraper import ScraperAgent
from agents.processor import ProcessorAgent
from agents.media import MediaAgent
from agents.composer import ComposerAgent
from config.settings import settings, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR
from models.schemas import PipelineRun, PipelineStatus, StepStatus


class OrchestratorAgent:
    """编排智能体：总指挥"""

    def __init__(self):
        self.name = "OrchestratorAgent"
        self.scraper = ScraperAgent()
        self.processor = ProcessorAgent()
        self.media = MediaAgent()
        self.composer = ComposerAgent()

    def run(
        self,
        news_count: int = 1,
        style: str = "realism",
        target_length: int = 30000,
        target_scene_count: int = 1800,
        news_index: int = 0,
    ) -> PipelineRun:
        """
        执行完整的流水线

        Args:
            news_count: 抓取新闻条数
            style: 小说风格
            target_length: 目标字数
            target_scene_count: 目标分镜数
            news_index: 选择第几条新闻进行改写

        Returns:
            PipelineRun 流水线运行记录
        """
        pipeline = PipelineRun(status=PipelineStatus.RUNNING)
        pipeline.current_step = "初始化"

        logger.info(f"[{self.name}] ========== 流水线启动 ==========")

        try:
            # ===== 阶段1: 抓取 =====
            pipeline.current_step = "scraping"
            pipeline.scraping_status = StepStatus.RUNNING
            logger.info(f"[{self.name}] 阶段1: 抓取新闻")

            news_list = self.scraper.run(count=news_count)
            pipeline.raw_news_list = news_list
            pipeline.scraping_status = StepStatus.COMPLETED

            if not news_list:
                raise RuntimeError("未抓取到任何新闻")

            # 选择要处理的新闻
            selected_news = news_list[min(news_index, len(news_list) - 1)]
            pipeline.raw_news_id = selected_news.id
            logger.info(f"[{self.name}] 选中新闻: {selected_news.title[:50]}...")

            # ===== 阶段2: 处理（脱敏+改写+分镜） =====
            pipeline.current_step = "processing"
            logger.info(f"[{self.name}] 阶段2: 处理新闻")

            # 2.1 脱敏
            pipeline.sanitization_status = StepStatus.RUNNING
            from skills.remove_pii import remove_pii
            sanitized = remove_pii(text=selected_news.content)
            sanitized.original_news_id = selected_news.id
            pipeline.sanitized_news_list = [sanitized]
            pipeline.sanitized_news_id = sanitized.id
            pipeline.sanitization_status = StepStatus.COMPLETED

            # 2.2 小说化改写
            pipeline.novel_writing_status = StepStatus.RUNNING
            from skills.rewrite_novel import rewrite_as_novel
            novel = rewrite_as_novel(
                text=sanitized.sanitized_content,
                style=style,
                target_length=target_length,
            )
            novel.sanitized_news_id = sanitized.id
            pipeline.novel_draft = novel
            pipeline.novel_id = novel.id
            pipeline.novel_writing_status = StepStatus.COMPLETED

            # 2.3 分镜脚本生成
            pipeline.scene_splitting_status = StepStatus.RUNNING
            from skills.split_scenes import split_into_scenes
            scenes = split_into_scenes(
                novel_text=novel.full_text,
                target_scene_count=target_scene_count,
            )
            for scene in scenes:
                scene.novel_id = novel.id
            pipeline.scenes = scenes
            pipeline.total_scenes = len(scenes)
            pipeline.scene_splitting_status = StepStatus.COMPLETED

            # ===== 阶段3: 媒体生成 =====
            pipeline.current_step = "media_generation"
            logger.info(f"[{self.name}] 阶段3: 媒体生成")

            # 确保输出目录存在
            settings.ensure_dirs()
            output_dir = str(AUDIO_DIR).replace("audio", "")

            media_result = self.media.run(
                scenes=scenes,
                character_sheet=novel.character_sheet,
                output_dir=output_dir,
            )
            audio_track, timeline, generated_images = media_result

            pipeline.audio_track = audio_track
            pipeline.timeline = timeline
            pipeline.audio_generation_status = StepStatus.COMPLETED

            pipeline.generated_images = generated_images
            pipeline.images_generated = sum(1 for img in generated_images if img.image_path)
            pipeline.image_generation_status = StepStatus.COMPLETED

            # ===== 阶段4: 视频合成 =====
            pipeline.current_step = "video_composition"
            pipeline.video_composition_status = StepStatus.RUNNING
            logger.info(f"[{self.name}] 阶段4: 视频合成")

            images_dir = str(IMAGES_DIR)
            audio_path = audio_track.audio_path

            final_video = self.composer.run(
                images_dir=images_dir,
                audio_path=audio_path,
                timeline=timeline,
                scenes=scenes,
                add_subtitles=settings.VIDEO_ADD_SUBTITLES,
                transition=settings.VIDEO_TRANSITION,
            )

            pipeline.final_video = final_video
            pipeline.video_composition_status = StepStatus.COMPLETED

            # ===== 完成 =====
            pipeline.status = PipelineStatus.COMPLETED
            pipeline.completed_at = datetime.now()
            pipeline.current_step = "completed"

            logger.info(
                f"[{self.name}] ========== 流水线完成 ==========\n"
                f"  新闻: {selected_news.title[:50]}\n"
                f"  小说: {novel.word_count}字\n"
                f"  分镜: {len(scenes)}个\n"
                f"  图片: {pipeline.images_generated}张\n"
                f"  视频: {final_video.video_path}\n"
                f"  时长: {final_video.duration:.1f}秒"
            )

        except Exception as e:
            pipeline.status = PipelineStatus.FAILED
            pipeline.error_message = str(e)
            pipeline.completed_at = datetime.now()
            logger.error(f"[{self.name}] 流水线失败: {e}")
            raise

        return pipeline

    def run_single_step(self, step: str, **kwargs) -> any:
        """
        仅执行单个步骤（用于调试和测试）

        Args:
            step: 步骤名称 (scrape/process/media/compose)
            **kwargs: 步骤参数

        Returns:
            步骤执行结果
        """
        if step == "scrape":
            return self.scraper.run(**kwargs)
        elif step == "process":
            return self.processor.run(**kwargs)
        elif step == "media":
            return self.media.run(**kwargs)
        elif step == "compose":
            return self.composer.run(**kwargs)
        else:
            raise ValueError(f"未知步骤: {step}")