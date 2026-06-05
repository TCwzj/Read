"""
视频处理服务封装
基于FFmpeg
"""
import subprocess
from pathlib import Path
from typing import Optional

from loguru import logger

from config.settings import settings, VIDEO_DIR, TEMP_DIR


class VideoService:
    """视频处理服务"""

    def __init__(self):
        self._fps = settings.VIDEO_FPS
        self._crf = settings.VIDEO_CRF
        self._preset = settings.VIDEO_PRESET

    def compose_video(
        self,
        images_dir: str,
        audio_path: str,
        timeline: list[dict],
        output_path: str = "",
        transition: str = "crossfade",
        add_subtitles: bool = True,
        subtitles_data: Optional[list[dict]] = None,
    ) -> str:
        """
        根据时间轴将图片与音频合成视频

        Args:
            images_dir: 图片目录路径
            audio_path: 音频文件路径
            timeline: 时间轴数据
            output_path: 输出视频路径
            transition: 转场效果
            add_subtitles: 是否添加字幕
            subtitles_data: 字幕数据

        Returns:
            输出视频路径
        """
        output_path = output_path or str(VIDEO_DIR / "final_video.mp4")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 第一步: 生成 FFmpeg concat 文件
        concat_path = str(TEMP_DIR / "concat.txt")
        TEMP_DIR.mkdir(parents=True, exist_ok=True)

        concat_content = ""
        for entry in timeline:
            scene_id = entry.get("scene_id", 0)
            duration = entry.get("duration", 1.5)
            image_path = str(Path(images_dir) / f"scene_{scene_id:04d}.png")

            # 检查图片是否存在
            if not Path(image_path).exists():
                logger.warning(f"图片不存在: {image_path}，使用黑色占位")
                self._create_black_frame(image_path)

            concat_content += f"file '{image_path}'\n"
            concat_content += f"duration {duration}\n"

        with open(concat_path, "w", encoding="utf-8") as f:
            f.write(concat_content)

        # 第二步: 生成字幕文件（可选）
        subtitle_path = ""
        if add_subtitles and subtitles_data:
            subtitle_path = self._generate_srt(subtitles_data, str(TEMP_DIR / "subtitles.srt"))

        # 第三步: FFmpeg 合成
        cmd = self._build_ffmpeg_command(
            concat_path=concat_path,
            audio_path=audio_path,
            output_path=output_path,
            subtitle_path=subtitle_path if add_subtitles else "",
        )

        try:
            logger.info(f"开始视频合成: {len(timeline)}帧")
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=3600,  # 1小时超时
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg合成失败: {result.stderr}")
                raise RuntimeError(f"视频合成失败: {result.stderr}")

            logger.info(f"视频合成完成: {output_path}")
            return output_path

        except subprocess.TimeoutExpired:
            logger.error("视频合成超时")
            raise
        except Exception as e:
            logger.error(f"视频合成异常: {e}")
            raise

    def _build_ffmpeg_command(
        self,
        concat_path: str,
        audio_path: str,
        output_path: str,
        subtitle_path: str = "",
    ) -> str:
        """构建FFmpeg命令"""
        # 视频滤镜
        vf_parts = [f"scale=1920:1080", f"fps={self._fps}"]

        if subtitle_path:
            # 烧入字幕
            vf_parts.append(f"subtitles='{subtitle_path}'")

        vf_str = ",".join(vf_parts)

        cmd = (
            f'ffmpeg -y '
            f'-f concat -safe 0 -i "{concat_path}" '
            f'-i "{audio_path}" '
            f'-vf "{vf_str}" '
            f'-c:v libx264 -preset {self._preset} -crf {self._crf} '
            f'-c:a aac -b:a 192k '
            f'-shortest '
            f'"{output_path}"'
        )

        return cmd

    def _generate_srt(
        self,
        subtitles_data: list[dict],
        output_path: str,
    ) -> str:
        """
        生成SRT字幕文件

        Args:
            subtitles_data: 字幕数据列表，每条包含scene_id, start_time, end_time, narration
            output_path: 输出路径

        Returns:
            字幕文件路径
        """
        srt_content = ""
        for i, sub in enumerate(subtitles_data, 1):
            start = self._format_srt_time(sub["start_time"])
            end = self._format_srt_time(sub["end_time"])
            text = sub.get("narration", "")
            srt_content += f"{i}\n{start} --> {end}\n{text}\n\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        logger.debug(f"字幕文件生成: {output_path}")
        return output_path

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """将秒数格式化为SRT时间格式 HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _create_black_frame(output_path: str, width: int = 1920, height: int = 1080):
        """创建黑色占位帧"""
        try:
            from PIL import Image
            img = Image.new("RGB", (width, height), (0, 0, 0))
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path)
        except ImportError:
            logger.warning("Pillow未安装，无法创建黑色占位帧")

    def post_process(
        self,
        video_path: str,
        output_path: str = "",
        intro_path: str = "",
        outro_path: str = "",
        background_music_path: str = "",
        bgm_volume: float = 0.2,
    ) -> str:
        """
        视频后处理：添加片头片尾、背景音乐等

        Args:
            video_path: 原始视频路径
            output_path: 输出路径
            intro_path: 片头视频路径
            outro_path: 片尾视频路径
            background_music_path: 背景音乐路径
            bgm_volume: 背景音乐音量 (0.0-1.0)

        Returns:
            处理后的视频路径
        """
        output_path = output_path or str(VIDEO_DIR / "final_processed.mp4")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        current_input = video_path

        # 添加片头片尾
        if intro_path or outro_path:
            concat_list = []
            if intro_path:
                concat_list.append(intro_path)
            concat_list.append(current_input)
            if outro_path:
                concat_list.append(outro_path)

            # 生成concat文件
            temp_concat = str(TEMP_DIR / "post_concat.txt")
            with open(temp_concat, "w", encoding="utf-8") as f:
                for path in concat_list:
                    f.write(f"file '{path}'\n")

            temp_output = str(TEMP_DIR / "with_intro_outro.mp4")
            cmd = f'ffmpeg -y -f concat -safe 0 -i "{temp_concat}" -c copy "{temp_output}"'
            subprocess.run(cmd, shell=True, check=True)
            current_input = temp_output

        # 添加背景音乐
        if background_music_path:
            temp_output = str(TEMP_DIR / "with_bgm.mp4")
            cmd = (
                f'ffmpeg -y '
                f'-i "{current_input}" '
                f'-stream_loop -1 -i "{background_music_path}" '
                f'-filter_complex "[1:a]volume={bgm_volume}[bgm];[0:a][bgm]amix=inputs=2:duration=first[aout]" '
                f'-map 0:v -map "[aout]" '
                f'-c:v copy -c:a aac -b:a 192k '
                f'-shortest "{temp_output}"'
            )
            subprocess.run(cmd, shell=True, check=True)
            current_input = temp_output

        # 最终复制到输出路径
        if current_input != output_path:
            import shutil
            shutil.copy2(current_input, output_path)

        logger.info(f"视频后处理完成: {output_path}")
        return output_path

    def get_video_info(self, video_path: str) -> dict:
        """
        获取视频信息

        Args:
            video_path: 视频文件路径

        Returns:
            视频信息字典
        """
        cmd = (
            f'ffprobe -v quiet -print_format json -show_format -show_streams "{video_path}"'
        )
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            import json
            info = json.loads(result.stdout)

            duration = float(info.get("format", {}).get("duration", 0))
            file_size = int(info.get("format", {}).get("size", 0))

            # 获取视频流信息
            video_stream = next(
                (s for s in info.get("streams", []) if s["codec_type"] == "video"),
                {},
            )
            width = video_stream.get("width", 0)
            height = video_stream.get("height", 0)

            return {
                "duration": duration,
                "resolution": f"{width}x{height}",
                "file_size": file_size,
            }
        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            return {}


# 全局服务实例
video_service = VideoService()