"""
Composer Agent（合成智能体）
负责图片+音频合成视频
"""
from loguru import logger

from skills.compose_video import compose_video
from skills.post_process import post_process_video
from config.settings import settings
from models.schemas import TimelineEntry, GeneratedImage, FinalVideo


class ComposerAgent:
    """合成智能体：剪辑师"""

    def __init__(self):
        self.name = "ComposerAgent"

    def run(
        self,
        images_dir: str,
        audio_path: str,
        timeline: list[TimelineEntry],
        scenes: list | None = None,
        add_subtitles: bool = True,
        transition: str = "crossfade",
    ) -> FinalVideo:
        """
        执行视频合成流程：合成 → 后处理

        Args:
            images_dir: 图片目录路径
            audio_path: 音频文件路径
            timeline: 时间轴数据
            scenes: 分镜列表（用于生成字幕）
            add_subtitles: 是否添加字幕
            transition: 转场效果

        Returns:
            FinalVideo 最终视频
        """
        logger.info(f"[{self.name}] 开始视频合成")

        # 准备字幕数据
        subtitles_data = None
        if add_subtitles and scenes:
            subtitles_data = [
                {
                    "scene_id": scene.scene_id,
                    "narration": scene.narration,
                }
                for scene in scenes
            ]

        # 步骤1: 视频合成
        logger.info(f"[{self.name}] 步骤1: 视频合成")
        video = compose_video(
            images_dir=images_dir,
            audio_path=audio_path,
            timeline=timeline,
            transition=transition,
            add_subtitles=add_subtitles,
            subtitles_data=subtitles_data,
        )

        # 步骤2: 视频后处理（可选）
        # TODO: 添加片头片尾、背景音乐等
        # final = post_process_video(video_path=video.video_path)

        logger.info(
            f"[{self.name}] 视频合成完成: {video.video_path}, "
            f"时长{video.duration:.1f}秒"
        )

        return video