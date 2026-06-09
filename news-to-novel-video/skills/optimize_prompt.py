"""
Skill 6: optimize_image_prompt
优化分镜中的画面描述，使其更适合图片生成模型
"""
from loguru import logger

from config.settings import settings
from services.llm_service import llm_service
from models.schemas import Scene


def optimize_image_prompt(
    raw_prompt: str,
    style_preset: str = "cinematic_realistic",
    previous_scene_description: str = "",
    character_sheet: str = "",
) -> dict:
    """
    优化画面描述为高质量的AI图片生成提示词

    Args:
        raw_prompt: 原始画面描述
        style_preset: 全局风格预设
        previous_scene_description: 上一个分镜的画面描述
        character_sheet: 角色设定表

    Returns:
        包含prompt和negative_prompt的字典
    """
    # 获取风格后缀
    style_suffix = settings.IMAGE_STYLE_SUFFIXES.get(
        style_preset, settings.IMAGE_STYLE_SUFFIXES["cinematic_realistic"]
    )

    # 如果原始提示词为空，返回默认提示词
    if not raw_prompt or not raw_prompt.strip():
        return {
            "prompt": f"A calm scene, {style_suffix}",
            "negative_prompt": settings.IMAGE_NEGATIVE_PROMPT,
        }

    # 使用LLM优化提示词
    try:
        optimized = _llm_optimize(
            raw_prompt, style_preset, previous_scene_description, character_sheet
        )
    except Exception as e:
        logger.warning(f"LLM提示词优化失败，使用基本拼接: {e}")
        optimized = raw_prompt

    # 拼接完整提示词
    full_prompt = f"{optimized}, {style_suffix}"

    return {
        "prompt": full_prompt,
        "negative_prompt": settings.IMAGE_NEGATIVE_PROMPT,
    }


def optimize_prompts_batch(
    scenes: list[Scene],
    style_preset: str = "cinematic_realistic",
    character_sheet: str = "",
) -> list[dict]:
    """
    批量优化分镜提示词

    Args:
        scenes: 分镜列表
        style_preset: 风格预设
        character_sheet: 角色设定表

    Returns:
        优化后的提示词列表
    """
    logger.info(f"开始批量优化提示词，共{len(scenes)}个分镜")

    optimized_prompts = []
    previous_description = ""

    for i, scene in enumerate(scenes):
        result = optimize_image_prompt(
            raw_prompt=scene.image_prompt,
            style_preset=style_preset,
            previous_scene_description=previous_description,
            character_sheet=character_sheet,
        )

        optimized_prompts.append(result)
        previous_description = result["prompt"]

        if (i + 1) % 100 == 0:
            logger.info(f"提示词优化进度: {i+1}/{len(scenes)}")

    logger.info(f"提示词批量优化完成")
    return optimized_prompts


def _llm_optimize(
    raw_prompt: str,
    style_preset: str,
    previous_scene_description: str,
    character_sheet: str,
) -> str:
    """使用LLM优化提示词"""
    result = llm_service.invoke_with_template(
        "image_prompt_optimize",
        {
            "raw_prompt": raw_prompt,
            "style_preset": style_preset,
            "previous_scene_description": previous_scene_description or "None",
            "character_sheet": character_sheet or "No specific character sheet provided.",
        },
    )

    # 提取优化后的提示词
    if "optimized_prompt:" in result.lower():
        parts = result.split("optimized_prompt:", 1)
        if len(parts) > 1:
            optimized = parts[1].strip()
            # 移除可能的引号
            optimized = optimized.strip("\"'")
            if optimized:
                return optimized

    # 如果格式不对，返回原始结果（取最后一行有效内容）
    lines = [l.strip() for l in result.strip().split("\n") if l.strip()]
    if lines:
        return lines[-1]

    return raw_prompt