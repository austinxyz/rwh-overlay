from __future__ import annotations
from dataclasses import dataclass
import logging
import requests

logger = logging.getLogger(__name__)

CNN_API_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; market-daily/1.0)"}


@dataclass(frozen=True)
class SentimentResult:
    score: int
    label: str
    prev_score: int


def fetch_sentiment() -> SentimentResult | None:
    try:
        resp = requests.get(CNN_API_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        fg = data["fear_and_greed"]
        return SentimentResult(
            score=int(fg["score"]),
            label=fg["rating"],
            prev_score=int(fg["previous_close"]),
        )
    except Exception as e:
        logger.warning("sentiment fetch failed: %s", e)
        return None
