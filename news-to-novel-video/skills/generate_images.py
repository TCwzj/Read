"""
Skill 7: generate_images
批量生成图片
"""
from loguru import logger

from config.settings import settings
from services.image_service import image_service
from models.schemas import Scene, GeneratedImage


def generate_images(
    scenes: list[Scene],
    output_dir: str = "",
    width: int = 1920,
    height: int = 1080,
    batch_size: int = 5,
) -> list[GeneratedImage]:
    """
    根据分镜提示词批量生成图片

    Args:
        scenes: 分镜列表（需已优化提示词）
        output_dir: 输出目录
        width: 图片宽度
        height: 图片高度
        batch_size: 每批并发数量

    Returns:
        生成的图片列表
    """
    logger.info(f"开始批量生成图片，共{len(scenes)}个分镜")

    # 准备提示词列表
    prompts = []
    for scene in scenes:
        prompts.append({
            "prompt": scene.image_prompt,
            "negative_prompt": scene.negative_prompt or settings.IMAGE_NEGATIVE_PROMPT,
        })

    # 调用图片生成服务
    image_paths = image_service.generate_batch_sync(
        prompts=prompts,
        output_dir=output_dir,
        width=width,
        height=height,
        batch_size=batch_size,
    )

    # 构建GeneratedImage列表
    generated_images = []
    for i, (scene, path) in enumerate(zip(scenes, image_paths)):
        generated_images.append(GeneratedImage(
            scene_id=scene.scene_id,
            image_path=path,
            prompt_used=scene.image_prompt,
            generation_params={
                "width": width,
                "height": height,
                "negative_prompt": scene.negative_prompt,
            },
            quality_score=1.0 if path else 0.0,
        ))

    success_count = sum(1 for img in generated_images if img.image_path)
    logger.info(f"图片批量生成完成: 成功{success_count}/{len(scenes)}")

    return generated_images