from __future__ import annotations
from unittest.mock import patch, MagicMock
from scripts.market.sentiment import fetch_sentiment, SentimentResult

SAMPLE_JSON = {
    "fear_and_greed": {
        "score": 42.0,
        "rating": "Fear",
        "previous_close": 47.0,
    }
}


def test_fetch_sentiment_parses_score():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_JSON
    with patch("scripts.market.sentiment.requests.get", return_value=mock_resp):
        result = fetch_sentiment()
    assert result is not None
    assert result.score == 42
    assert result.label == "Fear"
    assert result.prev_score == 47


def test_fetch_sentiment_returns_none_on_error():
    with patch("scripts.market.sentiment.requests.get", side_effect=Exception("timeout")):
        result = fetch_sentiment()
    assert result is None


def test_fetch_sentiment_returns_none_on_missing_key():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"unexpected": "data"}
    with patch("scripts.market.sentiment.requests.get", return_value=mock_resp):
        result = fetch_sentiment()
    assert result is None
