"""
Skill 5: generate_audio
将分镜旁白文本通过TTS转为语音，生成完整音频和时间轴
"""
from loguru import logger

from config.settings import settings
from services.tts_service import tts_service
from models.schemas import Scene, AudioTrack, TimelineEntry


def generate_audio(
    scenes: list[Scene],
    voice_type: str = "narrator_male",
    speed: float = 1.0,
    output_dir: str = "",
) -> dict:
    """
    将分镜旁白文本通过TTS转为语音，生成完整音频文件和分镜时间轴

    Args:
        scenes: 分镜列表
        voice_type: 语音类型
        speed: 语速
        output_dir: 输出目录

    Returns:
        包含audio_path, total_duration, timeline的字典
    """
    logger.info(f"开始音频生成，{len(scenes)}个分镜，语音类型: {voice_type}")

    # 将Scene对象转为字典列表
    scenes_data = [
        {
            "scene_id": scene.scene_id,
            "narration": scene.narration,
        }
        for scene in scenes
    ]

    # 调用TTS服务
    result = tts_service.synthesize_scenes_sync(
        scenes=scenes_data,
        output_dir=output_dir,
        voice_type=voice_type,
        speed=speed,
        sentence_pause_ms=settings.TTS_SENTENCE_PAUSE_MS,
    )

    # 转换时间轴为TimelineEntry对象
    timeline = [
        TimelineEntry(
            scene_id=entry["scene_id"],
            start_time=entry["start_time"],
            end_time=entry["end_time"],
            duration=entry["duration"],
        )
        for entry in result.get("timeline", [])
    ]

    audio_track = AudioTrack(
        novel_id="",
        audio_path=result.get("audio_path", ""),
        total_duration=result.get("total_duration", 0.0),
        voice_type=voice_type,
    )

    logger.info(f"音频生成完成，总时长: {audio_track.total_duration:.1f}秒")

    return {
        "audio_track": audio_track,
        "timeline": timeline,
    }