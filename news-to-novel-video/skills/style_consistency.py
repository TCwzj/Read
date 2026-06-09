"""
Skill 9: ensure_style_consistency
确保生成的图片风格一致
"""
from loguru import logger

from config.settings import settings


def ensure_style_consistency(
    reference_image_path: str = "",
    target_image_path: str = "",
    character_sheet: str = "",
) -> dict:
    """
    确保生成的图片风格一致

    策略:
    1. 固定全局风格提示词后缀 - 确保所有图片使用相同的风格描述
    2. 角色一致性 - 通过角色设定表确保角色外观一致
    3. 色调一致性 - 使用相同的色调描述
    4. 种子控制 - 相似场景使用相近种子

    Args:
        reference_image_path: 参考图片路径
        target_image_path: 待检查图片路径
        character_sheet: 角色设定表

    Returns:
        包含score和suggestions的字典
    """
    logger.info("执行风格一致性检查")

    score = 1.0
    suggestions = []

    # 检查风格后缀是否统一
    style_suffix = settings.IMAGE_STYLE_SUFFIXES.get(
        settings.IMAGE_STYLE_PRESET, ""
    )
    if not style_suffix:
        score -= 0.3
        suggestions.append("建议设置统一的风格提示词后缀")

    # 检查负面提示词
    if not settings.IMAGE_NEGATIVE_PROMPT:
        score -= 0.2
        suggestions.append("建议设置统一的负面提示词")

    # 检查角色设定表
    if not character_sheet:
        score -= 0.2
        suggestions.append("建议提供角色设定表以确保角色外观一致")

    # TODO: 图像相似度检查（需要图像对比模型）
    # 可以使用 CLIP 模型计算图片间的风格相似度

    score = max(0.0, min(1.0, score))

    logger.info(f"风格一致性评分: {score:.2f}")

    return {
        "score": score,
        "suggestions": suggestions,
    }


def get_consistency_params() -> dict:
    """
    获取风格一致性参数

    Returns:
        包含style_suffix, negative_prompt的字典
    """
    return {
        "style_suffix": settings.IMAGE_STYLE_SUFFIXES.get(
            settings.IMAGE_STYLE_PRESET, ""
        ),
        "negative_prompt": settings.IMAGE_NEGATIVE_PROMPT,
        "style_preset": settings.IMAGE_STYLE_PRESET,
    }