"""
全局配置文件
支持配置不同的 LLM 后端、TTS 服务、图片生成服务等
"""
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class LLMConfig:
    """LLM 配置 - 支持多种后端"""
    # 提供商选择：openai, azure, anthropic, gemini, ollama, localapi
    PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    
    # API 配置
    API_KEY = os.getenv("LLM_API_KEY", "")
    API_BASE = os.getenv("LLM_API_BASE", None)  # 自定义 API 端点
    API_VERSION = os.getenv("LLM_API_VERSION", None)  # Azure API 版本
    
    # 模型配置
    MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-4o")
    TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    
    # 备用模型（当主模型失败时使用）
    FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", None)
    
    # 请求配置
    TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))
    MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取 LLM 配置字典"""
        return {
            "provider": cls.PROVIDER,
            "api_key": cls.API_KEY,
            "api_base": cls.API_BASE,
            "api_version": cls.API_VERSION,
            "model_name": cls.MODEL_NAME,
            "temperature": cls.TEMPERATURE,
            "max_tokens": cls.MAX_TOKENS,
            "timeout": cls.TIMEOUT,
            "max_retries": cls.MAX_RETRIES,
        }


class TTSConfig:
    """TTS 语音合成配置"""
    # 提供商选择：edge, azure, aliyun, chattts, openai
    PROVIDER = os.getenv("TTS_PROVIDER", "edge")
    
    # API 配置
    API_KEY = os.getenv("TTS_API_KEY", "")
    API_BASE = os.getenv("TTS_API_BASE", None)
    
    # 语音配置
    VOICE = os.getenv("TTS_VOICE", "zh-CN-XiaoxiaoNeural")  # Edge TTS 默认语音
    SPEED = float(os.getenv("TTS_SPEED", "1.0"))
    PITCH = int(os.getenv("TTS_PITCH", "0"))
    
    # 输出配置
    OUTPUT_FORMAT = os.getenv("TTS_FORMAT", "mp3")
    SAMPLE_RATE = int(os.getenv("TTS_SAMPLE_RATE", "24000"))


class ImageGenConfig:
    """图片生成配置"""
    # 提供商选择：stable_diffusion, dall-e, midjourney, comfiui, local
    PROVIDER = os.getenv("IMAGE_PROVIDER", "stable_diffusion")
    
    # API 配置
    API_KEY = os.getenv("IMAGE_API_KEY", "")
    API_BASE = os.getenv("IMAGE_API_BASE", "http://localhost:7860")  # SD WebUI 默认地址
    
    # 生成配置
    MODEL_NAME = os.getenv("IMAGE_MODEL", "sd_xl_base_1.0.safetensors")
    WIDTH = int(os.getenv("IMAGE_WIDTH", "1920"))
    HEIGHT = int(os.getenv("IMAGE_HEIGHT", "1080"))
    STEPS = int(os.getenv("IMAGE_STEPS", "30"))
    CFG_SCALE = float(os.getenv("IMAGE_CFG_SCALE", "7.0"))
    
    # 风格一致性配置
    USE_IP_ADAPTER = os.getenv("IMAGE_USE_IP_ADAPTER", "true").lower() == "true"
    USE_CONTROLNET = os.getenv("IMAGE_USE_CONTROLNET", "false").lower() == "true"
    FIXED_SEED = int(os.getenv("IMAGE_FIXED_SEED", "42"))
    
    # 批处理配置
    BATCH_SIZE = int(os.getenv("IMAGE_BATCH_SIZE", "4"))
    CONCURRENT_JOBS = int(os.getenv("IMAGE_CONCURRENT_JOBS", "2"))


class VideoConfig:
    """视频合成配置"""
    # 编码器配置
    VIDEO_CODEC = os.getenv("VIDEO_CODEC", "libx264")
    AUDIO_CODEC = os.getenv("AUDIO_CODEC", "aac")
    CRF = int(os.getenv("VIDEO_CRF", "23"))  # 质量参数，越小质量越高
    PRESET = os.getenv("VIDEO_PRESET", "medium")  # 编码速度
    
    # 输出配置
    RESOLUTION = os.getenv("VIDEO_RESOLUTION", "1920x1080")
    FPS = int(os.getenv("VIDEO_FPS", "30"))
    
    # FFmpeg 路径
    FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")


class ScraperConfig:
    """新闻抓取配置"""
    # 抓取配置
    HEADLESS = os.getenv("SCRAPER_HEADLESS", "true").lower() == "true"
    PROXY = os.getenv("SCRAPER_PROXY", None)
    USER_AGENT = os.getenv("SCRAPER_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # 反爬配置
    DELAY_BETWEEN_REQUESTS = float(os.getenv("SCRAPER_DELAY", "1.0"))
    MAX_RETRIES = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
    TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", "30000"))


class PipelineConfig:
    """流水线配置"""
    # 存储路径
    STORAGE_ROOT = os.getenv("STORAGE_ROOT", "./storage")
    
    # 子目录
    IMAGES_DIR = os.path.join(STORAGE_ROOT, "images")
    AUDIO_DIR = os.path.join(STORAGE_ROOT, "audio")
    VIDEO_DIR = os.path.join(STORAGE_ROOT, "video")
    TEMP_DIR = os.path.join(STORAGE_ROOT, "temp")
    
    # 流水线配置
    MAX_NEWS_COUNT = int(os.getenv("PIPELINE_MAX_NEWS", "10"))
    TARGET_SCENE_COUNT = int(os.getenv("PIPELINE_TARGET_SCENES", "1800"))
    TARGET_NOVEL_LENGTH = int(os.getenv("PIPELINE_TARGET_LENGTH", "30000"))
    
    # 质量检查
    ENABLE_QUALITY_CHECK = os.getenv("PIPELINE_QUALITY_CHECK", "true").lower() == "true"
    MIN_IMAGE_QUALITY = float(os.getenv("PIPELINE_MIN_IMAGE_QUALITY", "0.6"))


# 创建配置目录
os.makedirs(PipelineConfig.STORAGE_ROOT, exist_ok=True)
os.makedirs(PipelineConfig.IMAGES_DIR, exist_ok=True)
os.makedirs(PipelineConfig.AUDIO_DIR, exist_ok=True)
os.makedirs(PipelineConfig.VIDEO_DIR, exist_ok=True)
os.makedirs(PipelineConfig.TEMP_DIR, exist_ok=True)