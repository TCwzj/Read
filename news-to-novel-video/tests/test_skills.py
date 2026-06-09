"""
Skill模块单元测试
"""
import pytest
from unittest.mock import patch, MagicMock


class TestScrapeNews:
    """测试抓取新闻Skill"""

    def test_scrape_with_mock_data(self):
        """测试使用模拟数据抓取"""
        from skills.scrape_news import _get_mock_news
        result = _get_mock_news(3)
        assert len(result) == 3
        assert all(hasattr(news, "title") for news in result)
        assert all(hasattr(news, "content") for news in result)

    def test_scrape_default_count(self):
        """测试默认抓取条数"""
        from skills.scrape_news import _get_mock_news
        result = _get_mock_news()
        assert len(result) == 5

    def test_scrape_count_exceeds_available(self):
        """测试抓取条数超过可用数量"""
        from skills.scrape_news import _get_mock_news
        result = _get_mock_news(100)
        assert len(result) == 5


class TestRemovePII:
    """测试PII脱敏Skill"""

    def test_remove_phone(self):
        """测试电话号码脱敏"""
        from skills.remove_pii import remove_pii
        text = "联系电话13812345678"
        result = remove_pii(text=text, pii_types=["phone"])
        assert "[电话号码]" in result.sanitized_content
        assert "13812345678" not in result.sanitized_content

    def test_remove_id_number(self):
        """测试身份证号脱敏"""
        from skills.remove_pii import remove_pii
        text = "身份证号110101199001011234"
        result = remove_pii(text=text, pii_types=["id_number"])
        assert "[身份证号]" in result.sanitized_content

    def test_remove_email(self):
        """测试邮箱脱敏"""
        from skills.remove_pii import remove_pii
        text = "邮箱test@example.com"
        result = remove_pii(text=text, pii_types=["email"])
        assert "[电子邮箱]" in result.sanitized_content

    def test_confidence_score(self):
        """测试置信度评分"""
        from skills.remove_pii import remove_pii
        text = "张三的电话是13812345678"
        result = remove_pii(text=text, pii_types=["phone"])
        assert 0 <= result.confidence_score <= 1.0


class TestSplitScenes:
    """测试分镜拆分Skill"""

    def test_simple_split(self):
        """测试简单分句策略"""
        from skills.split_scenes import _simple_split
        text = "这是第一句话。这是第二句话。这是第三句话。"
        scenes = _simple_split(text, chapter=1, seconds_per_scene=1.5)
        assert len(scenes) > 0
        assert all(hasattr(s, "narration") for s in scenes)

    def test_split_text_into_chunks(self):
        """测试文本分块"""
        from skills.split_scenes import _split_text_into_chunks
        text = "段落1\n\n段落2\n\n段落3"
        chunks = _split_text_into_chunks(text, max_chars=10)
        assert len(chunks) >= 2


class TestOptimizePrompt:
    """测试提示词优化Skill"""

    def test_empty_prompt(self):
        """测试空提示词"""
        from skills.optimize_prompt import optimize_image_prompt
        result = optimize_image_prompt(raw_prompt="")
        assert "prompt" in result
        assert "negative_prompt" in result

    def test_optimize_returns_dict(self):
        """测试返回格式"""
        from skills.optimize_prompt import optimize_image_prompt
        result = optimize_image_prompt(raw_prompt="A man walking")
        assert isinstance(result, dict)
        assert "prompt" in result
        assert "negative_prompt" in result


class TestStyleConsistency:
    """测试风格一致性Skill"""

    def test_consistency_check(self):
        """测试一致性检查"""
        from skills.style_consistency import ensure_style_consistency
        result = ensure_style_consistency()
        assert "score" in result
        assert "suggestions" in result
        assert 0 <= result["score"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])