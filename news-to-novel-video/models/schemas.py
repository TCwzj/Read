"""
数据模型定义 - 使用 Pydantic 进行数据验证
"""
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


# ============ 枚举类型 ============

class PipelineStatus(str, Enum):
    """流水线状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(str, Enum):
    """步骤状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class NovelStyle(str, Enum):
    """小说风格"""
    REALISM = "realism"  # 现实主义
    SUSPENSE = "suspense"  # 悬疑
    LITERARY = "literary"  # 文艺
    POPULAR = "popular"  # 通俗


class EmotionType(str, Enum):
    """情绪类型"""
    NEUTRAL = "neutral"
    GLOOMY = "gloomy"
    TENSE = "tense"
    WARM = "warm"
    SAD = "sad"
    ANGRY = "angry"
    HOPEFUL = "hopeful"
    JOYFUL = "joyful"


# ============ 抓取阶段 ============

class RawNews(BaseModel):
    """原始新闻"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    hot_score: float = 0.0
    publish_time: Optional[datetime] = None
    source_url: str = ""
    scraped_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "某市一小区发生离奇纠纷",
                "content": "某市某小区近日发生了一起引人关注的纠纷事件...",
                "hot_score": 98000,
                "source_url": "https://www.toutiao.com/article/xxx"
            }
        }


# ============ 脱敏阶段 ============

class SanitizedNews(BaseModel):
    """脱敏后新闻"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_news_id: str
    sanitized_content: str
    replacements: List[Dict[str, str]] = Field(default_factory=list)
    confidence_score: float = 1.0


# ============ 改写阶段 ============

class NovelDraft(BaseModel):
    """小说稿"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sanitized_news_id: str
    outline: str = ""  # 小说大纲
    full_text: str  # 完整小说文本
    style: str = NovelStyle.REALISM.value
    word_count: int = 0
    character_sheet: str = ""  # 角色设定表


# ============ 分镜阶段 ============

class Scene(BaseModel):
    """分镜"""
    id: int  # 分镜序号 (1-1800)
    novel_id: str
    narration: str  # 旁白文本
    image_prompt: str  # 图片生成提示词（英文）
    negative_prompt: str = ""  # 负面提示词
    emotion: str = EmotionType.NEUTRAL.value  # 情绪标签
    chapter: int = 1  # 所属章节
    estimated_duration: float = 1.5  # 预估时长（秒）


# ============ 音频阶段 ============

class AudioTrack(BaseModel):
    """音频轨道"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    novel_id: str
    audio_path: str
    total_duration: float
    voice_type: str


class TimelineEntry(BaseModel):
    """时间轴条目"""
    scene_id: int
    start_time: float
    end_time: float
    duration: float


# ============ 图片阶段 ============

class GeneratedImage(BaseModel):
    """生成的图片"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scene_id: int
    image_path: str
    prompt_used: str
    generation_params: Dict[str, Any] = Field(default_factory=dict)
    quality_score: float = 1.0


# ============ 视频阶段 ============

class FinalVideo(BaseModel):
    """最终视频"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    novel_id: str
    video_path: str
    duration: float
    resolution: str = "1920x1080"
    file_size: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


# ============ 流水线状态追踪 ============

class PipelineRun(BaseModel):
    """流水线运行记录"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: PipelineStatus = PipelineStatus.PENDING
    
    # 各阶段状态
    scraping_status: StepStatus = StepStatus.PENDING
    sanitization_status: StepStatus = StepStatus.PENDING
    novel_writing_status: StepStatus = StepStatus.PENDING
    scene_splitting_status: StepStatus = StepStatus.PENDING
    audio_generation_status: StepStatus = StepStatus.PENDING
    image_generation_status: StepStatus = StepStatus.PENDING
    video_composition_status: StepStatus = StepStatus.PENDING
    
    # 进度追踪
    total_scenes: int = 0
    images_generated: int = 0
    current_step: str = ""
    
    # 关联数据 ID
    raw_news_id: Optional[str] = None
    sanitized_news_id: Optional[str] = None
    novel_id: Optional[str] = None
    
    # 时间记录
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None