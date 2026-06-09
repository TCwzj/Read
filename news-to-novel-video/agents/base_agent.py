"""
智能体基类 - 所有智能体的统一接口
每个智能体都可以使用 LLM 进行智能决策，并调用 Skill 完成任务
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from services.llm_service import BaseLLM, get_llm

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """智能体基类"""
    
    name: str = "base_agent"
    description: str = "基础智能体"
    
    def __init__(
        self, 
        llm_config: Optional[Dict[str, Any]] = None,
        skills: Optional[List] = None
    ):
        """
        初始化智能体
        
        Args:
            llm_config: LLM 配置，如果不传则使用全局配置
            skills: 技能列表，智能体可以调用的技能
        """
        self.llm: BaseLLM = get_llm(llm_config)
        self.skills = skills or []
        self.context: Dict[str, Any] = {}  # 智能体的上下文状态
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行智能体的主要任务
        
        Args:
            input_data: 输入数据
        
        Returns:
            执行结果
        """
        pass
    
    def register_skill(self, skill):
        """注册技能"""
        self.skills.append(skill)
        logger.info(f"智能体 {self.name} 注册技能：{skill.__name__}")
    
    def get_skill(self, skill_name: str):
        """根据名称获取技能"""
        for skill in self.skills:
            if skill.__name__ == skill_name:
                return skill
        raise ValueError(f"未找到技能：{skill_name}")
    
    def call_skill(self, skill_name: str, **kwargs) -> Any:
        """调用技能"""
        skill = self.get_skill(skill_name)
        logger.info(f"智能体 {self.name} 调用技能：{skill_name}")
        return skill(**kwargs)
    
    def think(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        使用 LLM 进行思考/决策
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示（角色设定）
        
        Returns:
            LLM 生成的回复
        """
        return self.llm.generate(prompt, system_prompt)
    
    def think_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用 LLM 进行结构化思考/决策
        
        Args:
            prompt: 用户提示
            schema: JSON Schema
        
        Returns:
            LLM 生成的结构化数据
        """
        return self.llm.generate_json(prompt, schema)
    
    def update_context(self, **kwargs):
        """更新上下文"""
        self.context.update(kwargs)
    
    def get_context(self, key: str, default=None):
        """获取上下文中的值"""
        return self.context.get(key, default)
    
    def clear_context(self):
        """清空上下文"""
        self.context = {}