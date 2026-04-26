from __future__ import annotations
from dataclasses import dataclass
import logging
import re
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

FINVIZ_URL = "https://finviz.com/news.ashx"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; market-daily/1.0)"}
_ONCLICK_RE = re.compile(r"trackAndOpenNews\(event,\s*\d+,\s*'([^']+)'\)")


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
        for row in soup.find_all("tr", class_="news_table-row"):
            m = _ONCLICK_RE.search(row.get("onclick", ""))
            if not m:
                continue
            url = m.group(1)
            a = row.find("a")
            title = a.get_text(strip=True) if a else row.get_text(strip=True)[:120]
            if title and url.startswith("http"):
                items.append(NewsItem(title=title, url=url))
            if len(items) >= max_items:
                break
        return items
    except Exception as e:
        logger.warning("news fetch failed: %s", e)
        return []
