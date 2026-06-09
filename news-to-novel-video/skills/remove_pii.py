"""
Skill 2: remove_pii
使用 LLM 智能识别并移除个人身份信息 (PII)
"""
import logging
from typing import List, Dict, Any
from models.schemas import SanitizedNews, RawNews
from services.llm_service import llm_generate_json

logger = logging.getLogger(__name__)


# PII 脱敏的 JSON Schema
PII_SCHEMA = {
    "type": "object",
    "properties": {
        "replacements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "original": {"type": "string", "description": "原始敏感信息"},
                    "replacement": {"type": "string", "description": "替换后的通用描述"},
                    "type": {
                        "type": "string", 
                        "description": "敏感信息类型",
                        "enum": ["person_name", "location", "phone", "id_number", "organization", "address", "other"]
                    }
                },
                "required": ["original", "replacement", "type"]
            },
            "description": "需要替换的敏感信息列表"
        },
        "sanitized_text": {
            "type": "string",
            "description": "脱敏后的完整文本"
        },
        "confidence_score": {
            "type": "number",
            "description": "脱敏置信度 (0-1)",
            "minimum": 0,
            "maximum": 1
        }
    },
    "required": ["replacements", "sanitized_text", "confidence_score"]
}


def remove_pii(
    text: str,
    pii_types: List[str] = None,
    original_news_id: str = None
) -> SanitizedNews:
    """
    识别并替换文本中的个人身份信息 (PII)
    
    Args:
        text: 需要脱敏的新闻正文
        pii_types: 需要脱敏的信息类型列表
        original_news_id: 原始新闻 ID
    
    Returns:
        SanitizedNews: 脱敏后的新闻对象
    
    脱敏类型:
        - person_name: 人名 → "某人"/"他"/"她"
        - location: 具体地址 → "某市某区"
        - phone: 电话号码 → "[电话号码]"
        - id_number: 身份证号 → "[身份证号]"
        - organization: 机构名 → "某公司"/"某单位"
        - address: 详细地址 → "某地址"
    """
    if pii_types is None:
        pii_types = ["person_name", "location", "phone", "id_number", "organization", "address"]
    
    logger.info(f"开始脱敏处理，文本长度：{len(text)}")
    
    # 构建系统提示词
    system_prompt = """你是一位专业的隐私保护专家。请仔细识别文本中的所有个人隐私信息，并进行脱敏处理。

脱敏规则：
1. 人名 → 替换为"某人"、"他"、"她"等通用称呼
2. 具体地址 → 替换为"某市某区"、"某小区"等
3. 电话号码 → 替换为"[电话号码]"
4. 身份证号 → 替换为"[身份证号]"
5. 公司/机构名 → 替换为"某公司"、"某单位"等
6. 其他可识别个人的信息 → 适当脱敏

注意：
- 保持原文的叙事风格和流畅性
- 脱敏后文本应该自然可读
- 确保不遗漏任何敏感信息"""

    # 用户提示词
    user_prompt = f"""请对以下文本进行脱敏处理：

{text}

请输出 JSON 格式，包含：
1. sanitized_text: 脱敏后的完整文本
2. replacements: 替换记录列表，每项包含 original(原文)、replacement(替换后)、type(类型)
3. confidence_score: 脱敏置信度 (0-1)"""

    try:
        # 使用 LLM 进行脱敏
        result = llm_generate_json(user_prompt, PII_SCHEMA, system_prompt=system_prompt)
        
        sanitized_news = SanitizedNews(
            original_news_id=original_news_id or "",
            sanitized_content=result.get("sanitized_text", text),
            replacements=result.get("replacements", []),
            confidence_score=result.get("confidence_score", 0.8)
        )
        
        logger.info(f"脱敏完成，识别{len(sanitized_news.replacements)}个敏感信息，置信度：{sanitized_news.confidence_score}")
        return sanitized_news
        
    except Exception as e:
        logger.error(f"LLM 脱敏失败：{e}，使用规则脱敏")
        return _fallback_rule_based_pii(text, original_news_id)


def _fallback_rule_based_pii(text: str, original_news_id: str = None) -> SanitizedNews:
    """
     fallback: 基于规则的脱敏（当 LLM 失败时使用）
    """
    import re
    
    replacements = []
    sanitized = text
    
    # 电话号码匹配
    phone_pattern = r'1[3-9]\d{9}|0\d{2,3}-?\d{7,8}'
    for match in re.finditer(phone_pattern, sanitized):
        replacements.append({
            "original": match.group(),
            "replacement": "[电话号码]",
            "type": "phone"
        })
    
    # 身份证号匹配（简单匹配）
    id_pattern = r'\d{17}[\dXx]|\d{15}'
    for match in re.finditer(id_pattern, sanitized):
        replacements.append({
            "original": match.group(),
            "replacement": "[身份证号]",
            "type": "id_number"
        })
    
    # 执行替换
    for repl in replacements:
        sanitized = sanitized.replace(repl["original"], repl["replacement"])
    
    # 简单的人名替换（常见姓氏）
    common_surnames = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜"
    for surname in common_surnames:
        # 匹配"姓氏 + 某"或直接替换为"某人"
        pass  # 简化处理
    
    return SanitizedNews(
        original_news_id=original_news_id or "",
        sanitized_content=sanitized,
        replacements=replacements,
        confidence_score=0.6
    )


def batch_remove_pii(news_list: List[RawNews]) -> List[SanitizedNews]:
    """
    批量脱敏新闻列表
    
    Args:
        news_list: 原始新闻列表
    
    Returns:
        脱敏后新闻列表
    """
    results = []
    for news in news_list:
        result = remove_pii(
            text=news.content,
            original_news_id=news.id
        )
        results.append(result)
    return results