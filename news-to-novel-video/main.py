"""
新闻转小说视频系统 - 主入口
=============================

使用方法:
    1. 配置环境变量 (复制 .env.example 为 .env 并填写)
    2. 运行：python main.py

或者作为模块导入:
    from agents.orchestrator import OrchestratorAgent
    orchestrator = OrchestratorAgent()
    result = orchestrator.execute({"count": 5, "style": "realism"})
"""
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from agents.orchestrator import OrchestratorAgent
from agents.processor import ProcessorAgent
from agents.media import MediaAgent
from agents.composer import ComposerAgent
from config.settings import LLMConfig

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/pipeline_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="7 days",
    level="DEBUG",
    encoding="utf-8"
)

log = logging.getLogger(__name__)


def main():
    """主函数"""
    print("=" * 60)
    print("新闻转小说视频系统 v1.0")
    print("=" * 60)
    
    # 检查配置
    if not LLMConfig.API_KEY:
        print("\n⚠️  警告：未配置 LLM_API_KEY!")
        print("请复制 .env.example 为 .env 并填写 API 密钥\n")
    else:
        print(f"\n✅ LLM 配置：{LLMConfig.PROVIDER} / {LLMConfig.MODEL_NAME}")
    
    # 创建智能体
    print("\n正在初始化智能体...")
    
    orchestrator = OrchestratorAgent()
    processor = ProcessorAgent()
    media = MediaAgent()
    composer = ComposerAgent()
    
    # 设置子智能体
    orchestrator.set_sub_agents(
        scraper=None,  # 暂不使用独立抓取智能体
        processor=processor,
        media=media,
        composer=composer
    )
    
    print("✅ 智能体初始化完成\n")
    
    # 执行流水线
    print("开始执行流水线...")
    print("-" * 60)
    
    result = orchestrator.execute({
        "count": 5,
        "category": "society",
        "style": "realism"
    })
    
    print("-" * 60)
    
    if result.get("success"):
        print(f"\n🎉 流水线执行完成!")
        print(f"   视频路径：{result.get('video_path')}")
        print(f"   视频时长：{result.get('duration', 0):.1f}秒")
    else:
        print(f"\n❌ 流水线执行失败：{result.get('error')}")
    
    return result


def run_with_config(count: int = 5, style: str = "realism"):
    """
    使用指定配置运行
    
    Args:
        count: 抓取新闻条数
        style: 小说风格 (realism/suspense/literary/popular)
    """
    orchestrator = OrchestratorAgent()
    processor = ProcessorAgent()
    media = MediaAgent()
    composer = ComposerAgent()
    
    orchestrator.set_sub_agents(
        scraper=None,
        processor=processor,
        media=media,
        composer=composer
    )
    
    return orchestrator.execute({
        "count": count,
        "category": "society",
        "style": style
    })


if __name__ == "__main__":
    main()