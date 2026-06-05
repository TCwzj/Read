"""
数据模型定义
基于架构设计文档中的数据模型设计
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ===== 枚举类型 =====
class PipelineStatus(str, Enum):
    """流水线状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class StepStatus(str, Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class NovelStyle(str, Enum):
    """小说风格"""
    REALISM = "realism"
    SUSPENSE = "suspense"
    LITERARY = "literary"
    POPULAR = "popular"


class EmotionType(str, Enum):
    """情绪标签"""
    GLOOMY = "gloomy"
    TENSE = "tense"
    WARM = "warm"
    SAD = "sad"
    ANGRY = "angry"
    HOPEFUL = "hopeful"
    CALM = "calm"
    FEARFUL = "fearful"
    SURPRISED = "surprised"
    ROMANTIC = "romantic"
    MYSTERIOUS = "mysterious"
    DRAMATIC = "dramatic"


class TransitionType(str, Enum):
    """转场效果"""
    CUT = "cut"
    CROSSFADE = "crossfade"
    DISSOLVE = "dissolve"
    SLIDE = "slide"


# ===== 抓取阶段 =====
class RawNews(BaseModel):
    """原始新闻"""
    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    title: str
    content: str
    hot_score: float = 0.0
    publish_time: Optional[datetime] = None
    source_url: str = ""
    scraped_at: datetime = Field(default_factory=datetime.now)


# ===== 脱敏阶段 =====
class PIIReplacement(BaseModel):
    """PII替换记录"""
    original: str
    replacement: str
    type: str  # name, phone, address, id_number, organization


class SanitizedNews(BaseModel):
    """脱敏后新闻"""
    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    original_news_id: str
    sanitized_content: str
    replacements: list[PIIReplacement] = Field(default_factory=list)
    confidence_score: float = 0.0


# ===== 改写阶段 =====
class NovelOutline(BaseModel):
    """小说大纲"""
    character_sheet: str = ""  # 角色设定表
    plot_summary: str = ""     # 情节概要
    chapters: list[str] = Field(default_factory=list)  # 章节大纲列表


class NovelDraft(BaseModel):
    """小说稿"""
    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    sanitized_news_id: str
    outline: str = ""            # 小说大纲（文本形式）
    full_text: str = ""          # 完整小说文本
    style: NovelStyle = NovelStyle.REALISM
    word_count: int = 0
    character_sheet: str = ""    # 角色设定表（用于图片生成一致性）
    chapters: list[str] = Field(default_factory=list)  # 各章文本


# ===== 分镜阶段 =====
class Scene(BaseModel):
    """分镜"""
    scene_id: int                          # 分镜序号 (1-1800)
    novel_id: str = ""
    narration: str                         # 旁白文本
    image_prompt: str = ""                 # 图片生成提示词
    negative_prompt: str = ""              # 负面提示词
    emotion: EmotionType = EmotionType.CALM  # 情绪标签
    chapter: int = 1                       # 所属章节
    estimated_duration: float = 1.5        # 预估时长（秒）


# ===== 音频阶段 =====
class AudioTrack(BaseModel):
    """音频轨道"""
    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    novel_id: str = ""
    audio_path: str = ""
    total_duration: float = 0.0
    voice_type: str = "narrator_male"


class TimelineEntry(BaseModel):
    """时间轴条目"""
    scene_id: int
    start_time: float
    end_time: float
    duration: float


# ===== 图片阶段 =====
class GeneratedImage(BaseModel):
    """生成的图片"""
    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    scene_id: int
    image_path: str = ""
    prompt_used: str = ""
    generation_params: dict = Field(default_factory=dict)
    quality_score: float = 0.0


# ===== 视频阶段 =====
class FinalVideo(BaseModel):
    """最终视频"""
    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    novel_id: str = ""
    video_path: str = ""
    duration: float = 0.0
    resolution: str = "1920x1080"
    file_size: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


# ===== 流程状态追踪 =====
class PipelineRun(BaseModel):
    """流水线运行记录"""
    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
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

    # 关联数据ID
    raw_news_id: Optional[str] = None
    sanitized_news_id: Optional[str] = None
    novel_id: Optional[str] = None

    # 时间记录
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    # 中间结果存储
    raw_news_list: list[RawNews] = Field(default_factory=list)
    sanitized_news_list: list[SanitizedNews] = Field(default_factory=list)
    novel_draft: Optional[NovelDraft] = None
    scenes: list[Scene] = Field(default_factory=list)
    audio_track: Optional[AudioTrack] = None
    timeline: list[TimelineEntry] = Field(default_factory=list)
    generated_images: list[GeneratedImage] = Field(default_factory=list)
    final_video: Optional[FinalVideo] = None