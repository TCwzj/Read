"""
Skill 10: post_process_video
视频后处理：添加片头片尾、背景音乐、字幕样式优化
"""
from loguru import logger

from services.video_service import video_service
from models.schemas import FinalVideo


def post_process_video(
    video_path: str,
    output_path: str = "",
    intro_path: str = "",
    outro_path: str = "",
    background_music_path: str = "",
    bgm_volume: float = 0.2,
) -> FinalVideo:
    """
    视频后处理

    Args:
        video_path: 原始视频文件路径
        output_path: 输出路径
        intro_path: 片头视频路径
        outro_path: 片尾视频路径
        background_music_path: 背景音乐路径
        bgm_volume: 背景音乐音量 (0.0-1.0)

    Returns:
        FinalVideo 处理后的视频对象
    """
    logger.info(f"开始视频后处理: {video_path}")

    processed_path = video_service.post_process(
        video_path=video_path,
        output_path=output_path,
        intro_path=intro_path,
        outro_path=outro_path,
        background_music_path=background_music_path,
        bgm_volume=bgm_volume,
    )

    # 获取视频信息
    video_info = video_service.get_video_info(processed_path)

    final_video = FinalVideo(
        novel_id="",
        video_path=processed_path,
        duration=video_info.get("duration", 0.0),
        resolution=video_info.get("resolution", "1920x1080"),
        file_size=video_info.get("file_size", 0),
    )

    logger.info(f"视频后处理完成: {processed_path}, 时长: {final_video.duration:.1f}秒")

    return final_video