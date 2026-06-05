"""
TTS语音合成服务封装
基于Edge TTS（免费，中文质量好）
"""
import asyncio
from pathlib import Path
from typing import Optional

from loguru import logger

from config.settings import settings, AUDIO_DIR


class TTSService:
    """TTS语音合成服务"""

    def __init__(self):
        self._voice_map = settings.TTS_VOICE_MAP

    def get_voice_name(self, voice_type: str) -> str:
        """获取Edge TTS的语音名称"""
        return self._voice_map.get(voice_type, "zh-CN-YunxiNeural")

    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice_type: str = "narrator_male",
        speed: float = 1.0,
    ) -> str:
        """
        将文本合成为语音

        Args:
            text: 要合成的文本
            output_path: 输出文件路径
            voice_type: 语音类型
            speed: 语速（1.0为正常）

        Returns:
            输出文件路径
        """
        import edge_tts

        voice = self.get_voice_name(voice_type)
        rate = f"{'+'
                       if speed > 1 else ''}{int((speed - 1) * 100)}%"

        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(output_path)

        logger.debug(f"TTS合成完成: {output_path}")
        return output_path

    async def synthesize_scenes(
        self,
        scenes: list[dict],
        output_dir: Optional[str] = None,
        voice_type: str = "narrator_male",
        speed: float = 1.0,
        sentence_pause_ms: int = 300,
    ) -> dict:
        """
        批量合成分镜旁白，生成完整音频和时间轴

        Args:
            scenes: 分镜列表，每条包含narration字段
            output_dir: 输出目录
            voice_type: 语音类型
            speed: 语速
            sentence_pause_ms: 句间停顿（毫秒）

        Returns:
            包含audio_path, total_duration, timeline的字典
        """
        import edge_tts
        from pydub import AudioSegment

        output_dir = output_dir or str(AUDIO_DIR)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        voice = self.get_voice_name(voice_type)
        rate = f"{'+' if speed > 1 else ''}{int((speed - 1) * 100)}%"

        timeline = []
        audio_segments = []
        current_time = 0.0

        # 逐条生成音频片段
        for i, scene in enumerate(scenes):
            narration = scene.get("narration", "")
            if not narration.strip():
                continue

            # 生成单条音频
            segment_path = str(Path(output_dir) / f"scene_{i:04d}.mp3")
            communicate = edge_tts.Communicate(narration, voice, rate=rate)
            await communicate.save(segment_path)

            # 加载音频片段
            segment = AudioSegment.from_mp3(segment_path)
            duration_sec = len(segment) / 1000.0

            # 记录时间轴
            timeline.append({
                "scene_id": scene.get("scene_id", i),
                "start_time": current_time,
                "end_time": current_time + duration_sec,
                "duration": duration_sec,
            })

            audio_segments.append(segment)
            current_time += duration_sec

            # 添加句间停顿
            pause = AudioSegment.silent(duration=sentence_pause_ms)
            audio_segments.append(pause)
            current_time += sentence_pause_ms / 1000.0

        # 拼接所有片段
        if audio_segments:
            full_audio = audio_segments[0]
            for seg in audio_segments[1:]:
                full_audio += seg

            # 导出完整音频
            full_audio_path = str(Path(output_dir) / "full_audio.mp3")
            full_audio.export(full_audio_path, format="mp3")

            total_duration = len(full_audio) / 1000.0
        else:
            full_audio_path = ""
            total_duration = 0.0

        logger.info(f"TTS批量合成完成: {len(timeline)}条, 总时长{total_duration:.1f}秒")

        return {
            "audio_path": full_audio_path,
            "total_duration": total_duration,
            "timeline": timeline,
        }

    def synthesize_sync(
        self,
        text: str,
        output_path: str,
        voice_type: str = "narrator_male",
        speed: float = 1.0,
    ) -> str:
        """同步版本的TTS合成"""
        return asyncio.run(
            self.synthesize(text, output_path, voice_type, speed)
        )

    def synthesize_scenes_sync(
        self,
        scenes: list[dict],
        output_dir: Optional[str] = None,
        voice_type: str = "narrator_male",
        speed: float = 1.0,
        sentence_pause_ms: int = 300,
    ) -> dict:
        """同步版本的批量TTS合成"""
        return asyncio.run(
            self.synthesize_scenes(
                scenes, output_dir, voice_type, speed, sentence_pause_ms
            )
        )


# 全局服务实例
tts_service = TTSService()