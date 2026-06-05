"""
Skill 3: rewrite_as_novel
将脱敏后的新闻改写为小说体裁
"""
from loguru import logger

from config.settings import settings
from services.llm_service import llm_service
from models.schemas import NovelDraft, NovelStyle


def rewrite_as_novel(
    text: str,
    style: str = "realism",
    target_length: int = 30000,
) -> NovelDraft:
    """
    将脱敏后的新闻改写为小说体裁

    Args:
        text: 脱敏后的新闻正文
        style: 小说风格 (realism/suspense/literary/popular)
        target_length: 目标字数

    Returns:
        NovelDraft 小说稿对象
    """
    logger.info(f"开始小说改写，风格: {style}, 目标字数: {target_length}")

    chapters = settings.NOVEL_CHAPTERS
    words_per_chapter = settings.NOVEL_WORDS_PER_CHAPTER

    # 第一步：生成大纲
    logger.info("第一步：生成小说大纲...")
    outline_result = _generate_outline(text, style, chapters)
    logger.info(f"大纲生成完成，角色设定: {outline_result.get('character_sheet', '')[:100]}...")

    character_sheet = outline_result.get("character_sheet", "")
    plot_summary = outline_result.get("plot_summary", "")
    chapter_outlines = outline_result.get("chapters", [])

    if not chapter_outlines:
        # 如果大纲解析失败，生成默认章节
        chapter_outlines = [f"第{i+1}章" for i in range(chapters)]

    # 第二步：逐章扩写
    logger.info(f"第二步：逐章扩写，共{len(chapter_outlines)}章...")
    novel_chapters = []
    previous_summary = ""

    for i, chapter_outline in enumerate(chapter_outlines):
        logger.info(f"扩写第{i+1}/{len(chapter_outlines)}章...")

        chapter_text = _write_chapter(
            chapter_outline=chapter_outline,
            style=style,
            words_per_chapter=words_per_chapter,
            character_sheet=character_sheet,
            previous_summary=previous_summary,
        )
        novel_chapters.append(chapter_text)

        # 更新前文概要（取最后200字）
        previous_summary = chapter_text[-200:] if len(chapter_text) > 200 else chapter_text

        logger.info(f"第{i+1}章完成，字数: {len(chapter_text)}")

    # 第三步：合并
    full_text = "\n\n".join(novel_chapters)
    total_words = len(full_text)

    logger.info(f"小说改写完成，总字数: {total_words}")

    return NovelDraft(
        sanitized_news_id="",
        outline=str(outline_result),
        full_text=full_text,
        style=NovelStyle(style),
        word_count=total_words,
        character_sheet=character_sheet,
        chapters=novel_chapters,
    )


def _generate_outline(text: str, style: str, chapters: int) -> dict:
    """生成小说大纲"""
    prompt = f"""你是一位资深小说家。请将以下新闻改写为{style}风格的小说大纲。

要求:
- 保留核心冲突和情节走向
- 增加人物性格刻画
- 设计合理的情节转折
- 规划为约{chapters}章，每章约{settings.NOVEL_WORDS_PER_CHAPTER}字
- 每章需要包含具体的场景和动作描写

请按以下JSON格式输出:
{{
  "character_sheet": "角色设定表，描述每个角色的外貌、性格、背景",
  "plot_summary": "情节概要",
  "chapters": ["第1章大纲...", "第2章大纲...", ...]
}}

原始新闻:
{text}"""

    result = llm_service.invoke(prompt)

    try:
        outline = llm_service.invoke_json(prompt)
        if isinstance(outline, dict) and "chapters" in outline:
            return outline
    except Exception:
        pass

    # 解析失败，返回基本结构
    return {
        "character_sheet": "角色设定待补充",
        "plot_summary": result[:500],
        "chapters": [f"第{i+1}章" for i in range(chapters)],
    }


def _write_chapter(
    chapter_outline: str,
    style: str,
    words_per_chapter: int,
    character_sheet: str,
    previous_summary: str,
) -> str:
    """扩写单个章节"""
    style_desc = {
        "realism": "现实主义风格，注重细节描写，语言朴实有力",
        "suspense": "悬疑风格，设置悬念，节奏紧凑，步步为营",
        "literary": "文艺风格，语言优美，注重心理描写和意象",
        "popular": "通俗风格，情节曲折，节奏明快，通俗易懂",
    }

    result = llm_service.invoke_with_template(
        "novel_rewrite",
        {
            "style": style_desc.get(style, style),
            "chapters": "1",
            "words_per_chapter": str(words_per_chapter),
            "text": chapter_outline,
            "previous_summary": previous_summary or "这是第一章，还没有前文。",
        },
        system_prompt=f"你是一位{style}风格的小说家。请严格按照大纲扩写，保持风格一致。角色设定如下：{character_sheet}",
    )

    return result