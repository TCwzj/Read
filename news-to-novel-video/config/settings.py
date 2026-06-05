"""
全局配置模块
从环境变量读取配置，提供默认值
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# ===== 项目路径 =====
BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
IMAGES_DIR = STORAGE_DIR / "images"
AUDIO_DIR = STORAGE_DIR / "audio"
VIDEO_DIR = STORAGE_DIR / "video"
TEMP_DIR = STORAGE_DIR / "temp"
PROMPTS_DIR = BASE_DIR / "config" / "prompts"


class Settings:
    """全局配置类"""

    # ===== LLM 配置 =====
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))

    # ===== 抓取配置 =====
    SCRAPE_COUNT: int = int(os.getenv("SCRAPE_COUNT", "10"))
    SCRAPE_CATEGORY: str = os.getenv("SCRAPE_CATEGORY", "society")
    SCRAPE_HEADLESS: bool = os.getenv("SCRAPE_HEADLESS", "true").lower() == "true"
    SCRAPE_PROXY: str = os.getenv("SCRAPE_PROXY", "")

    # ===== 脱敏配置 =====
    PII_TYPES: list[str] = os.getenv(
        "PII_TYPES", "name,phone,address,id_number,organization"
    ).split(",")

    # ===== 小说改写配置 =====
    NOVEL_STYLE: str = os.getenv("NOVEL_STYLE", "realism")
    NOVEL_TARGET_LENGTH: int = int(os.getenv("NOVEL_TARGET_LENGTH", "30000"))
    NOVEL_CHAPTERS: int = int(os.getenv("NOVEL_CHAPTERS", "60"))
    NOVEL_WORDS_PER_CHAPTER: int = int(os.getenv("NOVEL_WORDS_PER_CHAPTER", "500"))

    # ===== 分镜配置 =====
    SCENE_TARGET_COUNT: int = int(os.getenv("SCENE_TARGET_COUNT", "1800"))
    SCENE_SECONDS_PER_SCENE: float = float(os.getenv("SCENE_SECONDS_PER_SCENE", "1.5"))

    # ===== TTS 配置 =====
    TTS_VOICE_TYPE: str = os.getenv("TTS_VOICE_TYPE", "narrator_male")
    TTS_SPEED: float = float(os.getenv("TTS_SPEED", "1.0"))
    TTS_SENTENCE_PAUSE_MS: int = int(os.getenv("TTS_SENTENCE_PAUSE_MS", "300"))
    TTS_PARAGRAPH_PAUSE_MS: int = int(os.getenv("TTS_PARAGRAPH_PAUSE_MS", "800"))

    # TTS语音映射
    TTS_VOICE_MAP: dict = {
        "narrator_male": "zh-CN-YunxiNeural",
        "narrator_female": "zh-CN-XiaoxiaoNeural",
        "storyteller": "zh-CN-YunjianNeural",
    }

    # ===== 图片生成配置 =====
    IMAGE_WIDTH: int = int(os.getenv("IMAGE_WIDTH", "1920"))
    IMAGE_HEIGHT: int = int(os.getenv("IMAGE_HEIGHT", "1080"))
    IMAGE_BATCH_SIZE: int = int(os.getenv("IMAGE_BATCH_SIZE", "5"))
    IMAGE_STYLE_PRESET: str = os.getenv("IMAGE_STYLE_PRESET", "cinematic_realistic")

    # 图片风格后缀
    IMAGE_STYLE_SUFFIXES: dict = {
        "cinematic_realistic": (
            "cinematic lighting, realistic photography, 16:9, high detail, "
            "Chinese urban setting, warm color palette, shallow depth of field"
        ),
        "dark_atmospheric": (
            "dark atmospheric lighting, moody, dramatic shadows, "
            "cinematic, 16:9, high contrast, film grain"
        ),
        "warm_literary": (
            "warm soft lighting, literary film style, gentle tones, "
            "16:9, shallow depth of field, natural light"
        ),
    }

    # 负面提示词
    IMAGE_NEGATIVE_PROMPT: str = (
        "cartoon, anime, painting, watermark, text, distorted face, "
        "extra fingers, low quality, blurry, deformed, disfigured, "
        "bad anatomy, bad proportions, duplicate, cropped"
    )

    # Stable Diffusion API 配置
    SD_API_URL: str = os.getenv("SD_API_URL", "http://127.0.0.1:7860")
    SD_API_ENABLED: bool = os.getenv("SD_API_ENABLED", "false").lower() == "true"

    # ===== 视频合成配置 =====
    VIDEO_TRANSITION: str = os.getenv("VIDEO_TRANSITION", "crossfade")
    VIDEO_ADD_SUBTITLES: bool = os.getenv("VIDEO_ADD_SUBTITLES", "true").lower() == "true"
    VIDEO_FPS: int = int(os.getenv("VIDEO_FPS", "30"))
    VIDEO_CRF: int = int(os.getenv("VIDEO_CRF", "23"))
    VIDEO_PRESET: str = os.getenv("VIDEO_PRESET", "medium")

    # ===== 任务队列配置（可选） =====
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # ===== 日志配置 =====
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def ensure_dirs(self):
        """确保所有存储目录存在"""
        for d in [STORAGE_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, TEMP_DIR]:
            d.mkdir(parents=True, exist_ok=True)


# 全局配置实例
settings = Settings()