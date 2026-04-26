from __future__ import annotations
from dataclasses import dataclass
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

FINVIZ_URL = "https://finviz.com/news.ashx"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; market-daily/1.0)"}


@dataclass(frozen=True)
class NewsItem:
    title: str
    url: str


def fetch_news(max_items: int = 5) -> list[NewsItem]:
    try:
        resp = requests.get(FINVIZ_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []
        for a in soup.select("table.fullview-news-outer a[href]"):
            title = a.get_text(strip=True)
            url = a["href"]
            if title and url.startswith("http"):
                items.append(NewsItem(title=title, url=url))
            if len(items) >= max_items:
                break
        return items
    except Exception as e:
        logger.warning("news fetch failed: %s", e)
        return []
