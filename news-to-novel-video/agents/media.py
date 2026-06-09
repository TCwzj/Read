"""
Media Agent（媒体智能体）
负责音频生成 + 图片生成
"""
from loguru import logger

from skills.generate_audio import generate_audio
from skills.optimize_prompt import optimize_image_prompt, optimize_prompts_batch
from skills.generate_images import generate_images
from skills.style_consistency import ensure_style_consistency
from config.settings import settings
from models.schemas import Scene, AudioTrack, TimelineEntry, GeneratedImage


class MediaAgent:
    """媒体智能体：制作人"""

    def __init__(self):
        self.name = "MediaAgent"

    def run(
        self,
        scenes: list[Scene],
        character_sheet: str = "",
        output_dir: str = "",
    ) -> tuple[AudioTrack, list[TimelineEntry], list[GeneratedImage]]:
        """
        执行完整媒体生成流程：音频生成 + 提示词优化 + 图片生成

        Args:
            scenes: 分镜列表
            character_sheet: 角色设定表
            output_dir: 输出目录

        Returns:
            (音频轨道, 时间轴, 生成图片列表)
        """
        logger.info(f"[{self.name}] 开始媒体生成，共{len(scenes)}个分镜")

        # 步骤1: 风格一致性检查
        logger.info(f"[{self.name}] 步骤1: 风格一致性检查")
        consistency = ensure_style_consistency(character_sheet=character_sheet)
        if consistency["score"] < 0.5:
            logger.warning(f"[{self.name}] 风格一致性评分较低: {consistency['score']:.2f}")
            for suggestion in consistency["suggestions"]:
                logger.warning(f"  - {suggestion}")

        # 步骤2: 优化图片提示词
        logger.info(f"[{self.name}] 步骤2: 优化图片提示词")
        optimized_prompts = optimize_prompts_batch(
            scenes=scenes,
            style_preset=settings.IMAGE_STYLE_PRESET,
            character_sheet=character_sheet,
        )

        # 更新分镜的提示词
        for scene, opt in zip(scenes, optimized_prompts):
            scene.image_prompt = opt["prompt"]
            scene.negative_prompt = opt["negative_prompt"]

        # 步骤3: TTS语音合成（可并行，但此处顺序执行）
        logger.info(f"[{self.name}] 步骤3: TTS语音合成")
        audio_result = generate_audio(
            scenes=scenes,
            voice_type=settings.TTS_VOICE_TYPE,
            speed=settings.TTS_SPEED,
            output_dir=output_dir,
        )
        audio_track = audio_result["audio_track"]
        timeline = audio_result["timeline"]

        # 步骤4: 批量图片生成
        logger.info(f"[{self.name}] 步骤4: 批量图片生成")
        generated_images = generate_images(
            scenes=scenes,
            output_dir=output_dir,
            width=settings.IMAGE_WIDTH,
            height=settings.IMAGE_HEIGHT,
            batch_size=settings.IMAGE_BATCH_SIZE,
        )

        logger.info(
            f"[{self.name}] 媒体生成完成: 音频{audio_track.total_duration:.1f}秒, "
            f"图片{sum(1 for img in generated_images if img.image_path)}张"
        )

        return audio_track, timeline, generated_images