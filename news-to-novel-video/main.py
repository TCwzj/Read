"""
新闻转小说视频系统 - 入口文件
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import click
from loguru import logger

from config.settings import settings
from pipeline.workflow import NewsToNovelWorkflow


@click.group()
def cli():
    """新闻转小说视频系统"""
    pass


@cli.command()
@click.option("--count", default=1, help="抓取新闻条数")
@click.option("--style", default="realism", help="小说风格 (realism/suspense/literary/popular)")
@click.option("--length", default=30000, help="目标字数")
@click.option("--scenes", default=1800, help="目标分镜数")
@click.option("--index", default=0, help="选择第几条新闻")
@click.option("--retries", default=3, help="最大重试次数")
def run(count, style, length, scenes, index, retries):
    """运行完整流水线：抓取 → 脱敏 → 改写 → 媒体生成 → 视频合成"""
    logger.info("启动新闻转小说视频系统")

    workflow = NewsToNovelWorkflow()

    try:
        pipeline = workflow.run_with_retry(
            max_retries=retries,
            news_count=count,
            style=style,
            target_length=length,
            target_scene_count=scenes,
            news_index=index,
        )

        if pipeline.status.value == "completed":
            logger.info("✅ 流水线执行成功！")
            if pipeline.final_video:
                logger.info(f"📹 视频文件: {pipeline.final_video.video_path}")
                logger.info(f"⏱️ 视频时长: {pipeline.final_video.duration:.1f}秒")
        else:
            logger.error(f"❌ 流水线执行失败: {pipeline.error_message}")

    except Exception as e:
        logger.error(f"❌ 系统异常: {e}")
        sys.exit(1)


@cli.command()
@click.option("--count", default=5, help="抓取条数")
def scrape(count):
    """仅执行新闻抓取"""
    from agents.scraper import ScraperAgent

    agent = ScraperAgent()
    news_list = agent.run(count=count)

    if not news_list:
        logger.warning("未抓取到任何新闻")
        return

    for i, news in enumerate(news_list):
        logger.info(f"{i+1}. [{news.hot_score:.0f}热度] {news.title}")
        logger.info(f"   正文: {news.content[:80]}...")


@cli.command()
@click.argument("text")
def pii(text):
    """测试PII脱敏"""
    from skills.remove_pii import remove_pii

    result = remove_pii(text=text)
    logger.info(f"脱敏结果: {result.sanitized_content}")
    logger.info(f"替换: {len(result.replacements)}处")
    logger.info(f"置信度: {result.confidence_score:.2f}")
    for rep in result.replacements:
        logger.info(f"  - [{rep.type}] {rep.original} → {rep.replacement}")


@cli.command()
@click.argument("text")
@click.option("--style", default="realism", help="小说风格")
def rewrite(text, style):
    """测试小说改写"""
    from skills.rewrite_novel import rewrite_as_novel

    result = rewrite_as_novel(text=text, style=style)
    logger.info(f"小说完成: {result.word_count}字")
    logger.info(f"前200字: {result.full_text[:200]}...")


@cli.command()
def check():
    """检查系统环境"""
    logger.info("检查系统环境...")

    # 检查Python版本
    logger.info(f"Python版本: {sys.version}")

    # 检查FFmpeg
    import subprocess
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        logger.info(f"FFmpeg: ✅ {result.stdout.split(chr(10))[0]}")
    except FileNotFoundError:
        logger.warning("FFmpeg: ❌ 未安装")

    # 检查API Key
    if settings.OPENAI_API_KEY:
        logger.info(f"OpenAI API Key: ✅ 已配置 ({settings.OPENAI_API_KEY[:8]}...)")
    else:
        logger.warning("OpenAI API Key: ❌ 未配置")

    # 检查目录
    settings.ensure_dirs()
    logger.info(f"输出目录: ✅ {settings.STORAGE_DIR}")

    logger.info("环境检查完成")


@cli.command()
def demo():
    """运行5个分镜的快速演示"""
    logger.info("===== 快速演示模式（5个分镜）=====")

    workflow = NewsToNovelWorkflow()
    pipeline = workflow.run(
        news_count=1,
        style="realism",
        target_length=5000,
        target_scene_count=5,
        news_index=0,
    )

    if pipeline.status.value == "completed":
        logger.info("✅ 演示完成！")
    else:
        logger.error(f"❌ 演示失败: {pipeline.error_message}")


if __name__ == "__main__":
    cli()