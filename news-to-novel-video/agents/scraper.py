"""
Scraper Agent（抓取智能体）
负责从今日头条抓取社会新闻
"""
from loguru import logger

from skills.scrape_news import scrape_toutiao_news
from models.schemas import RawNews


class ScraperAgent:
    """抓取智能体：信息采集员"""

    def __init__(self):
        self.name = "ScraperAgent"

    def run(self, count: int = 10, category: str = "society") -> list[RawNews]:
        """
        执行抓取任务

        Args:
            count: 抓取条数
            category: 新闻分类

        Returns:
            新闻列表
        """
        logger.info(f"[{self.name}] 开始抓取任务，目标{count}条{category}新闻")

        news_list = scrape_toutiao_news(count=count, category=category)

        # 过滤不适合的新闻
        filtered = self._filter_news(news_list)

        logger.info(f"[{self.name}] 抓取完成，获取{len(filtered)}条合适新闻")
        return filtered

    def _filter_news(self, news_list: list[RawNews]) -> list[RawNews]:
        """
        过滤不适合改写的新闻

        过滤规则:
        - 正文字数过少（<100字）
        - 标题包含敏感关键词
        """
        sensitive_keywords = ["涉政", "涉军", "涉恐", "涉暴"]

        filtered = []
        for news in news_list:
            # 字数检查
            if len(news.content) < 100:
                logger.debug(f"过滤: 正文过短 - {news.title[:30]}")
                continue

            # 敏感词检查
            if any(kw in news.title or kw in news.content for kw in sensitive_keywords):
                logger.debug(f"过滤: 包含敏感词 - {news.title[:30]}")
                continue

            filtered.append(news)

        return filtered