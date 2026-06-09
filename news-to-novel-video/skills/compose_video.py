"""
Skill 8: compose_video
将图片和音频合成视频
"""
from loguru import logger

from config.settings import settings
from services.video_service import video_service
from models.schemas import TimelineEntry, GeneratedImage, FinalVideo


def compose_video(
    images_dir: str,
    audio_path: str,
    timeline: list[TimelineEntry],
    output_path: str = "",
    transition: str = "crossfade",
    add_subtitles: bool = True,
    subtitles_data: list[dict] | None = None,
) -> FinalVideo:
    """
    根据时间轴将图片与音频对齐，合成最终视频

    Args:
        images_dir: 图片目录路径
        audio_path: 音频文件路径
        timeline: 时间轴数据
        output_path: 输出视频路径
        transition: 转场效果
        add_subtitles: 是否添加字幕
        subtitles_data: 字幕数据

    Returns:
        FinalVideo 最终视频对象
    """
    logger.info(f"开始视频合成，{len(timeline)}个时间轴条目")

    # 转换时间轴为字典列表
    timeline_data = [
        {
            "scene_id": entry.scene_id,
            "start_time": entry.start_time,
            "end_time": entry.end_time,
            "duration": entry.duration,
        }
        for entry in timeline
    ]

    # 调用视频合成服务
    video_path = video_service.compose_video(
        images_dir=images_dir,
        audio_path=audio_path,
        timeline=timeline_data,
        output_path=output_path,
        transition=transition,
        add_subtitles=add_subtitles,
        subtitles_data=subtitles_data,
    )

    # 获取视频信息
    video_info = video_service.get_video_info(video_path)

    final_video = FinalVideo(
        novel_id="",
        video_path=video_path,
        duration=video_info.get("duration", 0.0),
        resolution=video_info.get("resolution", "1920x1080"),
        file_size=video_info.get("file_size", 0),
    )

    logger.info(f"视频合成完成: {video_path}, 时长: {final_video.duration:.1f}秒")

    return final_video