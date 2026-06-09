"""
编排智能体 (Orchestrator Agent)
负责整个流水线的调度、状态管理和异常处理
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from agents.base_agent import BaseAgent
from models.schemas import PipelineRun, PipelineStatus, StepStatus

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """编排智能体 - 总指挥"""
    
    name = "orchestrator"
    description = "负责整体流程调度、状态管理和异常处理"
    
    def __init__(self, llm_config: Optional[Dict] = None):
        super().__init__(llm_config)
        
        # 子智能体（稍后注入）
        self.scraper_agent = None
        self.processor_agent = None
        self.media_agent = None
        self.composer_agent = None
        
        # 当前流水线状态
        self.current_run: Optional[PipelineRun] = None
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行完整的新闻转小说视频流水线
        
        Args:
            input_data: 输入参数，可包含:
                - count: 抓取新闻条数
                - category: 新闻分类
                - style: 小说风格
        """
        count = input_data.get("count", 10)
        category = input_data.get("category", "society")
        style = input_data.get("style", "realism")
        
        # 初始化流水线记录
        self.current_run = PipelineRun(
            status=PipelineStatus.RUNNING,
            started_at=datetime.now()
        )
        
        try:
            # Step 1: 抓取新闻
            logger.info("=== 开始执行 Step 1: 抓取新闻 ===")
            self.current_run.current_step = "scraping"
            news_list = self._step_scrape_news(count, category)
            self.current_run.raw_news_id = news_list[0]["id"] if news_list else None
            self.current_run.scraping_status = StepStatus.COMPLETED
            
            # Step 2: 脱敏处理
            logger.info("=== 开始执行 Step 2: 脱敏处理 ===")
            self.current_run.current_step = "sanitization"
            sanitized_news = self._step_remove_pii(news_list[0]["content"])
            self.current_run.sanitized_news_id = sanitized_news["id"]
            self.current_run.sanitization_status = StepStatus.COMPLETED
            
            # Step 3: 小说化改写
            logger.info("=== 开始执行 Step 3: 小说化改写 ===")
            self.current_run.current_step = "novel_writing"
            novel = self._step_rewrite_novel(sanitized_news["content"], style)
            self.current_run.novel_id = novel["id"]
            self.current_run.novel_writing_status = StepStatus.COMPLETED
            
            # Step 4: 分镜拆分
            logger.info("=== 开始执行 Step 4: 分镜拆分 ===")
            self.current_run.current_step = "scene_splitting"
            scenes = self._step_split_scenes(novel["content"])
            self.current_run.total_scenes = len(scenes)
            self.current_run.scene_splitting_status = StepStatus.COMPLETED
            
            # Step 5: 媒体生成（并行）
            logger.info("=== 开始执行 Step 5: 媒体生成 ===")
            self.current_run.current_step = "media_generation"
            audio_result = self._step_generate_audio(scenes)
            images_result = self._step_generate_images(scenes)
            self.current_run.audio_generation_status = StepStatus.COMPLETED
            self.current_run.image_generation_status = StepStatus.COMPLETED
            
            # Step 6: 视频合成
            logger.info("=== 开始执行 Step 6: 视频合成 ===")
            self.current_run.current_step = "video_composition"
            video_result = self._step_compose_video(audio_result, images_result)
            self.current_run.video_composition_status = StepStatus.COMPLETED
            
            # 完成
            self.current_run.status = PipelineStatus.COMPLETED
            self.current_run.completed_at = datetime.now()
            
            logger.info("🎉 流水线执行完成！")
            
            return {
                "success": True,
                "pipeline_run_id": self.current_run.id,
                "video_path": video_result.get("video_path"),
                "duration": video_result.get("duration")
            }
            
        except Exception as e:
            logger.exception(f"流水线执行失败：{e}")
            self.current_run.status = PipelineStatus.FAILED
            self.current_run.error_message = str(e)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _step_scrape_news(self, count: int, category: str) -> List[Dict]:
        """Step 1: 抓取新闻"""
        if self.scraper_agent:
            result = self.scraper_agent.execute({"count": count, "category": category})
            return result.get("news_list", [])
        
        # 直接调用 Skill
        from skills.scrape_news import scrape_toutiao_news
        news_list = scrape_toutiao_news(count=count, category=category)
        return [news.model_dump() if hasattr(news, 'model_dump') else news for news in news_list]
    
    def _step_remove_pii(self, text: str) -> Dict:
        """Step 2: 脱敏处理"""
        if self.processor_agent:
            return self.processor_agent.execute({"text": text, "task": "remove_pii"})
        
        from skills.remove_pii import remove_pii
        result = remove_pii(text=text)
        return result.model_dump() if hasattr(result, 'model_dump') else result
    
    def _step_rewrite_novel(self, text: str, style: str) -> Dict:
        """Step 3: 小说化改写"""
        if self.processor_agent:
            return self.processor_agent.execute({"text": text, "style": style, "task": "rewrite"})
        
        from skills.rewrite_novel import rewrite_as_novel
        result = rewrite_as_novel(text=text, style=style)
        return result.model_dump() if hasattr(result, 'model_dump') else result
    
    def _step_split_scenes(self, novel_text: str) -> List[Dict]:
        """Step 4: 分镜拆分"""
        if self.processor_agent:
            return self.processor_agent.execute({"novel_text": novel_text, "task": "split_scenes"})
        
        from skills.split_scenes import split_into_scenes
        scenes = split_into_scenes(novel_text=novel_text)
        return [s.model_dump() if hasattr(s, 'model_dump') else s for s in scenes]
    
    def _step_generate_audio(self, scenes: List[Dict]) -> Dict:
        """Step 5a: 音频生成"""
        if self.media_agent:
            return self.media_agent.execute({"scenes": scenes, "task": "audio"})
        
        from skills.generate_audio import generate_audio
        return generate_audio(scenes=scenes)
    
    def _step_generate_images(self, scenes: List[Dict]) -> Dict:
        """Step 5b: 图片生成"""
        if self.media_agent:
            return self.media_agent.execute({"scenes": scenes, "task": "images"})
        
        from skills.generate_images import generate_images
        return generate_images(scenes=scenes)
    
    def _step_compose_video(self, audio_result: Dict, images_result: Dict) -> Dict:
        """Step 6: 视频合成"""
        if self.composer_agent:
            return self.composer_agent.execute({
                "audio": audio_result,
                "images": images_result,
                "task": "compose"
            })
        
        from skills.compose_video import compose_video
        return compose_video(
            images_dir=images_result.get("images_dir"),
            audio_path=audio_result.get("audio_path"),
            timeline=audio_result.get("timeline", [])
        )
    
    def set_sub_agents(self, scraper, processor, media, composer):
        """设置子智能体"""
        self.scraper_agent = scraper
        self.processor_agent = processor
        self.media_agent = media
        self.composer_agent = composer
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        if not self.current_run:
            return {"status": "idle"}
        
        return {
            "status": self.current_run.status.value,
            "current_step": self.current_run.current_step,
            "progress": {
                "scraping": self.current_run.scraping_status.value,
                "sanitization": self.current_run.sanitization_status.value,
                "novel_writing": self.current_run.novel_writing_status.value,
                "scene_splitting": self.current_run.scene_splitting_status.value,
                "audio_generation": self.current_run.audio_generation_status.value,
                "image_generation": self.current_run.image_generation_status.value,
                "video_composition": self.current_run.video_composition_status.value,
            },
            "total_scenes": self.current_run.total_scenes,
            "images_generated": self.current_run.images_generated,
            "error": self.current_run.error_message
        }