"""
Skills - 提示词模板集合

每个 Skill 都是一个提示词模板 (.md 文件),供智能体使用 LLM 完成任务。

Skill 列表:
- scrape_news: 新闻抓取与解析
- remove_pii: PII 脱敏
- rewrite_novel: 小说化改写
- split_scenes: 分镜拆分
- optimize_prompt: 提示词优化
- generate_audio: TTS 参数生成
- generate_images: 图片质量检查
- compose_video: 视频合成决策
- style_consistency: 风格一致性检查
- post_process: 视频后处理与文案生成
"""

import os
from typing import Dict

# Skill 名称到模板文件的映射
SKILL_TEMPLATES: Dict[str, str] = {
    "scrape_news": "scrape_news.md",
    "remove_pii": "remove_pii.md",
    "rewrite_novel": "rewrite_novel.md",
    "split_scenes": "split_scenes.md",
    "optimize_prompt": "optimize_prompt.md",
    "generate_audio": "generate_audio.md",
    "generate_images": "generate_images.md",
    "compose_video": "compose_video.md",
    "style_consistency": "style_consistency.md",
    "post_process": "post_process.md",
}

# 获取当前模块所在目录
SKILLS_DIR = os.path.dirname(os.path.abspath(__file__))


def get_skill_path(skill_name: str) -> str:
    """
    获取指定 Skill 的模板文件路径

    Args:
        skill_name: Skill 名称，如 "remove_pii"

    Returns:
        Skill 模板文件的完整路径

    Raises:
        KeyError: 如果 Skill 不存在
    """
    if skill_name not in SKILL_TEMPLATES:
        raise KeyError(f"未知的 Skill: {skill_name}")

    return os.path.join(SKILLS_DIR, SKILL_TEMPLATES[skill_name])


def load_skill_template(skill_name: str) -> str:
    """
    加载指定 Skill 的提示词模板

    Args:
        skill_name: Skill 名称

    Returns:
        Skill 模板内容

    Raises:
        FileNotFoundError: 如果模板文件不存在
        KeyError: 如果 Skill 不存在
    """
    template_path = get_skill_path(skill_name)

    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def list_available_skills() -> list:
    """
    列出所有可用的 Skill

    Returns:
        Skill 名称列表
    """
    return list(SKILL_TEMPLATES.keys())


# 导出公共 API
__all__ = [
    "SKILL_TEMPLATES",
    "get_skill_path",
    "load_skill_template",
    "list_available_skills",
]