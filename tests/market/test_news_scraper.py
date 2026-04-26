from __future__ import annotations
import pytest
from unittest.mock import patch, MagicMock
from scripts.market.news_scraper import fetch_news, NewsItem

SAMPLE_HTML = """
<html><body>
<table class="fullview-news-outer">
  <tr><td>
    <span class="date">Apr-25-26</span>
    <a href="https://example.com/story1">Fed holds rates steady</a>
  </td></tr>
  <tr><td>
    <span class="date">Apr-25-26</span>
    <a href="https://example.com/story2">Nvidia leads chip rally</a>
  </td></tr>
</table>
</body></html>
"""


def test_fetch_news_parses_headlines():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = SAMPLE_HTML
    with patch("scripts.market.news_scraper.requests.get", return_value=mock_resp):
        items = fetch_news(max_items=5)
    assert len(items) == 2
    assert items[0].title == "Fed holds rates steady"
    assert items[0].url == "https://example.com/story1"


def test_fetch_news_returns_empty_on_error():
    with patch("scripts.market.news_scraper.requests.get", side_effect=Exception("timeout")):
        items = fetch_news(max_items=5)
    assert items == []


def test_fetch_news_respects_max_items():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = SAMPLE_HTML
    with patch("scripts.market.news_scraper.requests.get", return_value=mock_resp):
        items = fetch_news(max_items=1)
    assert len(items) == 1
