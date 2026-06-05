"""
Skill 1: scrape_toutiao_news
从今日头条社会新闻板块抓取热度最高的新闻
"""
from typing import Optional
from loguru import logger

from config.settings import settings
from models.schemas import RawNews


def scrape_toutiao_news(
    count: int = 10,
    category: str = "society",
) -> list[RawNews]:
    """
    从今日头条社会新闻板块抓取热度最高的社会新闻

    Args:
        count: 抓取条数，默认10
        category: 新闻分类，默认society

    Returns:
        新闻列表，每条包含标题、正文、热度值、发布时间
    """
    logger.info(f"开始抓取今日头条{category}新闻，目标{count}条")

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(
                headless=settings.SCRAPE_HEADLESS,
                proxy={"server": settings.SCRAPE_PROXY} if settings.SCRAPE_PROXY else None,
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # 访问今日头条新闻频道
            url = f"https://www.toutiao.com/ch/news_{category}/"
            logger.info(f"访问: {url}")
            page.goto(url, wait_until="networkidle", timeout=30000)

            # 等待新闻列表加载
            page.wait_for_selector(".feed-card-article-l", timeout=10000)

            # 滚动加载更多内容
            for _ in range(3):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(2000)

            # 解析新闻列表
            news_items = page.query_selector_all(".feed-card-article-l")
            logger.info(f"找到{len(news_items)}条新闻")

            results = []
            for item in news_items[:count]:
                try:
                    # 提取标题
                    title_el = item.query_selector("a.title")
                    title = title_el.inner_text().strip() if title_el else ""

                    # 提取链接
                    link = title_el.get_attribute("href") if title_el else ""
                    if link and not link.startswith("http"):
                        link = "https://www.toutiao.com" + link

                    # 提取热度
                    hot_el = item.query_selector(".feed-digg")
                    hot_score = 0.0
                    if hot_el:
                        hot_text = hot_el.inner_text().strip()
                        try:
                            hot_score = float(hot_text.replace("万", "000").replace("+", ""))
                        except ValueError:
                            hot_score = 0.0

                    if not title or not link:
                        continue

                    # 进入详情页抓取正文
                    detail_page = context.new_page()
                    try:
                        detail_page.goto(link, wait_until="networkidle", timeout=15000)
                        detail_page.wait_for_selector("article", timeout=5000)

                        # 提取正文
                        article_el = detail_page.query_selector("article")
                        content = article_el.inner_text().strip() if article_el else ""

                        if content:
                            news = RawNews(
                                title=title,
                                content=content,
                                hot_score=hot_score,
                                source_url=link,
                            )
                            results.append(news)
                            logger.debug(f"抓取成功: {title[:30]}...")

                    except Exception as e:
                        logger.warning(f"详情页抓取失败: {e}")
                    finally:
                        detail_page.close()

                    # 控制抓取速度
                    page.wait_for_timeout(1000)

                except Exception as e:
                    logger.warning(f"解析新闻条目失败: {e}")
                    continue

            browser.close()

        # 按热度排序
        results.sort(key=lambda x: x.hot_score, reverse=True)
        logger.info(f"抓取完成，成功获取{len(results)}条新闻")

    except ImportError:
        logger.warning("Playwright未安装，使用模拟数据")
        results = _get_mock_news(count)
    except Exception as e:
        logger.error(f"抓取失败: {e}")
        logger.info("使用模拟数据替代")
        results = _get_mock_news(count)

    return results


def _get_mock_news(count: int = 5) -> list[RawNews]:
    """生成模拟新闻数据（用于开发测试）"""
    mock_data = [
        RawNews(
            title="某市一小区发生离奇纠纷，业主与物业对簿公堂",
            content="某市某小区近日发生了一起引人关注的纠纷事件。据小区业主反映，物业公司未经业主同意，"
                     "擅自将小区公共区域出租给外部商户经营，所得收益也未按比例分配给业主。多名业主表示，"
                     "物业公司不仅服务质量下降，还频繁上调物业费，引发业主强烈不满。目前，部分业主已将"
                     "物业公司诉至法院，要求公开账目并返还违规收取的费用。法律专家指出，根据相关法规，"
                     "小区公共区域的经营收益应归全体业主所有，物业公司的行为涉嫌侵权。",
            hot_score=98000,
        ),
        RawNews(
            title="外卖骑手深夜救人引发社会关注",
            content="某市一名外卖骑手在深夜送餐途中，发现一名老人倒在路边不省人事。骑手当即停下电动车，"
                     "拨打急救电话并守在老人身边，直到救护车到达。事后，骑手因订单超时被扣款，但他的善举"
                     "被路人拍下并发到网上，引发广泛关注。外卖平台随后表示将免除其扣款，并给予奖励。"
                     "当地文明办也将其评为见义勇为先进个人。骑手表示，当时没想太多，就觉得人命最重要。",
            hot_score=87000,
        ),
        RawNews(
            title="农村留守儿童的暑假：一个人的留守时光",
            content="在某省某村，12岁的小明已经三年没有见到在外打工的父母了。每年暑假，他最大的期盼就是"
                     "父母能回来住几天，但今年父母因为工厂加班又无法回来。小明每天一个人写作业、做饭、"
                     "喂鸡，偶尔和村里的老人下棋。村里的留守儿童有十几个，他们的暑假大多在孤独中度过。"
                     "当地政府已开始组织暑期关爱活动，但覆盖面仍然有限。专家呼吁，需要更多社会力量关注"
                     "留守儿童的心理健康问题。",
            hot_score=76000,
        ),
        RawNews(
            title="社区食堂走红：3元一顿饭背后的暖心故事",
            content="在某市某社区，一家由社区志愿者运营的食堂近日走红网络。这里每顿饭只收3元，却能让"
                     "老人们吃上热乎可口的饭菜。食堂的运营经费主要来自社区捐赠和政府补贴，厨师和服务员"
                     "都是志愿者。每天中午，社区里的独居老人们会聚在这里，一边吃饭一边聊天，食堂成了他们"
                     "最重要的社交场所。发起人李阿姨说，看到老人们吃得开心，就是最大的满足。目前，已有"
                     "多个社区前来学习这一模式。",
            hot_score=65000,
        ),
        RawNews(
            title="年轻人回乡创业：从城市白领到乡村新农人",
            content="90后大学毕业生小张曾是一名城市白领，月薪过万。然而去年，他做出了一个让所有人意外的"
                     "决定：辞职回乡种地。起初，家人强烈反对，村民也不理解。但小张利用大学所学的农业技术，"
                     "在自家地里搞起了智慧农业，通过手机APP远程控制灌溉和施肥。他还开了直播，把种地过程"
                     "展示给网友看，没想到意外走红。如今，他的农场年收入已达30万元，还带动了周边十几户"
                     "农民增收。小张说，乡村不是年轻人的退路，而是新路。",
            hot_score=54000,
        ),
    ]
    return mock_data[:count]