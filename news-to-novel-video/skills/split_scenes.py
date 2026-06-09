"""
Skill 4: split_into_scenes
将小说文本拆分为分镜脚本
"""
import json
import re
from loguru import logger

from config.settings import settings
from services.llm_service import llm_service
from models.schemas import Scene, EmotionType


def split_into_scenes(
    novel_text: str,
    target_scene_count: int = 1800,
    seconds_per_scene: float = 1.5,
) -> list[Scene]:
    """
    将小说文本拆分为分镜脚本

    Args:
        novel_text: 小说全文
        target_scene_count: 目标分镜数量
        seconds_per_scene: 每个分镜的时长（秒）

    Returns:
        分镜列表
    """
    logger.info(f"开始分镜拆分，目标{target_scene_count}个分镜")

    # 如果小说文本过长，分段处理
    max_chars_per_chunk = 5000
    chunks = _split_text_into_chunks(novel_text, max_chars_per_chunk)
    logger.info(f"小说分为{len(chunks)}段处理")

    # 估算每段应产生的分镜数
    scenes_per_chunk = max(1, target_scene_count // len(chunks))

    all_scenes = []
    for i, chunk in enumerate(chunks):
        logger.info(f"处理第{i+1}/{len(chunks)}段...")
        chunk_scenes = _process_chunk(chunk, scenes_per_chunk, seconds_per_scene, i + 1)
        all_scenes.extend(chunk_scenes)
        logger.info(f"第{i+1}段完成，生成{len(chunk_scenes)}个分镜")

    # 重新编号
    for idx, scene in enumerate(all_scenes):
        scene.scene_id = idx + 1

    logger.info(f"分镜拆分完成，共{len(all_scenes)}个分镜")
    return all_scenes


def _split_text_into_chunks(text: str, max_chars: int) -> list[str]:
    """将长文本按段落拆分为块"""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            current_chunk += "\n\n" + para if current_chunk else para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def _process_chunk(
    chunk: str,
    target_count: int,
    seconds_per_scene: float,
    chapter: int,
) -> list[Scene]:
    """处理单个文本块，生成分镜"""
    result = llm_service.invoke_with_template(
        "scene_split",
        {
            "target_scene_count": str(target_count),
            "novel_text": chunk,
        },
    )

    # 尝试解析JSON输出
    scenes = _parse_scenes_result(result, chapter, seconds_per_scene)

    if not scenes:
        # 解析失败，使用简单分句策略
        scenes = _simple_split(chunk, chapter, seconds_per_scene)

    return scenes


def _parse_scenes_result(result: str, chapter: int, seconds_per_scene: float) -> list[Scene]:
    """解析LLM输出的分镜JSON"""
    scenes = []
    parsed = None

    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        try:
            match = re.search(r'\[.*\]', result, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

    try:
        if isinstance(parsed, list):
            for item in parsed:
                scene = _dict_to_scene(item, chapter, seconds_per_scene)
                if scene:
                    scenes.append(scene)
        elif isinstance(parsed, dict) and "scenes" in parsed:
            for item in parsed["scenes"]:
                scene = _dict_to_scene(item, chapter, seconds_per_scene)
                if scene:
                    scenes.append(scene)
    except Exception as e:
        logger.warning(f"分镜JSON解析失败: {e}")

    return scenes


def _dict_to_scene(data: dict, chapter: int, seconds_per_scene: float) -> Scene | None:
    """将字典转换为Scene对象"""
    try:
        narration = data.get("narration", "")
        if not narration:
            return None

        emotion_str = data.get("emotion", "calm")
        try:
            emotion = EmotionType(emotion_str)
        except ValueError:
            emotion = EmotionType.CALM

        # 根据旁白字数估算时长（语速约4字/秒）
        estimated_duration = len(narration) / 4.0
        estimated_duration = max(estimated_duration, seconds_per_scene)

        return Scene(
            scene_id=data.get("scene_id", 0),
            narration=narration,
            image_prompt=data.get("image_prompt", ""),
            negative_prompt="",
            emotion=emotion,
            chapter=data.get("chapter", chapter),
            estimated_duration=estimated_duration,
        )
    except Exception as e:
        logger.warning(f"分镜数据转换失败: {e}")
        return None


def _simple_split(text: str, chapter: int, seconds_per_scene: float) -> list[Scene]:
    """简单分句策略（备选方案）"""
    # 按句号、问号、感叹号分句
    sentences = re.split(r'[。！？]', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    scenes = []
    for i, sentence in enumerate(sentences):
        if i % 2 == 0:
            narration = sentence + "。"
            if i + 1 < len(sentences):
                narration += sentences[i + 1] + "。"

            estimated_duration = len(narration) / 4.0

            scenes.append(Scene(
                scene_id=len(scenes) + 1,
                narration=narration.strip(),
                image_prompt="",
                negative_prompt="",
                emotion=EmotionType.CALM,
                chapter=chapter,
                estimated_duration=max(estimated_duration, seconds_per_scene),
            ))

    return scenes