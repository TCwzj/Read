"""
Skill 2: remove_pii
识别并替换新闻中的个人身份信息（PII）
"""
import re
from loguru import logger

from services.llm_service import llm_service
from models.schemas import SanitizedNews, PIIReplacement


# 正则表达式模式
REGEX_PATTERNS = {
    "phone": (r"1[3-9]\d{9}", "[电话号码]"),
    "id_number": (r"\d{17}[\dXx]", "[身份证号]"),
    "email": (r"[\w.-]+@[\w.-]+\.\w+", "[电子邮箱]"),
    "bank_card": (r"\d{16,19}", "[银行卡号]"),
    "license_plate": (r"[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁][A-Z][A-Z0-9]{5}", "[车牌号]"),
}


def remove_pii(
    text: str,
    pii_types: list[str] | None = None,
) -> SanitizedNews:
    """
    识别并替换文本中的个人身份信息

    Args:
        text: 需要脱敏的新闻正文文本
        pii_types: 需要脱敏的信息类型列表

    Returns:
        SanitizedNews 脱敏后新闻对象
    """
    pii_types = pii_types or ["name", "phone", "address", "id_number", "organization"]
    logger.info(f"开始PII脱敏，类型: {pii_types}")

    all_replacements = []
    sanitized_text = text

    # 第一步：正则匹配（电话、身份证、邮箱等）
    for pii_type in pii_types:
        if pii_type in REGEX_PATTERNS:
            pattern, replacement = REGEX_PATTERNS[pii_type]
            matches = re.findall(pattern, sanitized_text)
            for match in matches:
                all_replacements.append(PIIReplacement(
                    original=match,
                    replacement=replacement,
                    type=pii_type,
                ))
                sanitized_text = sanitized_text.replace(match, replacement)

    # 第二步：NER识别（人名、地名、机构名）
    try:
        ner_replacements = _ner_recognize(text, pii_types)
        for rep in ner_replacements:
            sanitized_text = sanitized_text.replace(rep.original, rep.replacement)
            all_replacements.append(rep)
    except Exception as e:
        logger.warning(f"NER识别失败，跳过: {e}")

    # 第三步：LLM复核
    try:
        llm_result = _llm_review(sanitized_text)
        if llm_result:
            for rep in llm_result:
                sanitized_text = sanitized_text.replace(rep.original, rep.replacement)
                all_replacements.append(rep)
    except Exception as e:
        logger.warning(f"LLM复核失败，跳过: {e}")

    # 计算置信度
    confidence = _calculate_confidence(text, sanitized_text, all_replacements)

    logger.info(f"PII脱敏完成，替换{len(all_replacements)}处，置信度{confidence:.2f}")

    return SanitizedNews(
        original_news_id="",
        sanitized_content=sanitized_text,
        replacements=all_replacements,
        confidence_score=confidence,
    )


def _ner_recognize(text: str, pii_types: list[str]) -> list[PIIReplacement]:
    """使用NER模型识别实体"""
    replacements = []

    try:
        import spacy
        nlp = spacy.load("zh_core_web_sm")
        doc = nlp(text)

        entity_type_map = {
            "PERSON": "name",
            "GPE": "address",
            "LOC": "address",
            "ORG": "organization",
        }

        replacement_map = {
            "name": "某人",
            "address": "某地",
            "organization": "某单位",
        }

        for ent in doc.ents:
            mapped_type = entity_type_map.get(ent.label_, "")
            if mapped_type in pii_types:
                replacements.append(PIIReplacement(
                    original=ent.text,
                    replacement=replacement_map.get(mapped_type, "某"),
                    type=mapped_type,
                ))

    except ImportError:
        logger.debug("spaCy未安装，跳过NER识别")
    except OSError:
        logger.debug("中文NER模型未下载，跳过NER识别")

    return replacements


def _llm_review(text: str) -> list[PIIReplacement]:
    """使用LLM复核脱敏结果"""
    replacements = []

    result = llm_service.invoke_with_template(
        "pii_removal",
        {"text": text},
    )

    # 尝试解析结果
    try:
        import json
        data = json.loads(result)
        if isinstance(data, dict) and "replacements" in data:
            for rep in data["replacements"]:
                replacements.append(PIIReplacement(
                    original=rep.get("original", ""),
                    replacement=rep.get("replacement", ""),
                    type=rep.get("type", "unknown"),
                ))
    except (json.JSONDecodeError, KeyError):
        logger.debug("LLM复核结果解析失败，忽略")

    return replacements


def _calculate_confidence(
    original: str,
    sanitized: str,
    replacements: list[PIIReplacement],
) -> float:
    """计算脱敏置信度"""
    if not replacements:
        return 1.0

    # 基于替换数量和文本长度的比例
    ratio = len(replacements) / max(len(original) / 10, 1)

    # 正则匹配的置信度高，NER中等，LLM较低
    type_weights = {
        "phone": 0.95,
        "id_number": 0.95,
        "email": 0.95,
        "bank_card": 0.95,
        "license_plate": 0.95,
        "name": 0.80,
        "address": 0.75,
        "organization": 0.70,
    }

    weighted_sum = sum(
        type_weights.get(r.type, 0.5) for r in replacements
    )
    confidence = weighted_sum / max(len(replacements), 1)

    return min(confidence, 1.0)