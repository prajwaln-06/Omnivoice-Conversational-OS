import logging
import os
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class IndicBERTSentiment:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or os.getenv(
            "INDICBERT_SENTIMENT_MODEL",
            "monsoon-nlp/indic-bert-native-sentiment",
        )
        self.pipeline = None
        if TRANSFORMERS_AVAILABLE:
            try:
                tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
                self.pipeline = pipeline(
                    "sentiment-analysis",
                    model=model,
                    tokenizer=tokenizer,
                )
                logger.info("[Sentiment] Loaded IndicBERT model %s", self.model_name)
            except Exception as exc:
                logger.warning(
                    "[Sentiment] Could not load IndicBERT sentiment model %s: %s",
                    self.model_name,
                    exc,
                )
                self.pipeline = None

    def analyze(self, text: str) -> Dict[str, Any]:
        normalized_text = text.strip()
        if not normalized_text:
            return {"label": "neutral", "score": 0.0, "empathy_flag": False}

        if self.pipeline:
            try:
                result = self.pipeline(normalized_text[:512])
                if isinstance(result, list) and result:
                    label = str(result[0].get("label", "neutral")).lower()
                    score = float(result[0].get("score", 0.0))
                    empathy_flag = label in {
                        "negative",
                        "anxious",
                        "frustrated",
                        "sad",
                    }
                    return {
                        "label": label,
                        "score": score,
                        "empathy_flag": empathy_flag,
                    }
            except Exception as exc:
                logger.warning("[Sentiment] pipeline failed: %s", exc)

        label, score = self._heuristic_sentiment(normalized_text)
        return {
            "label": label,
            "score": score,
            "empathy_flag": label in {"anxious", "frustrated"},
        }

    def _heuristic_sentiment(self, text: str) -> tuple[str, float]:
        text_lower = text.lower()
        if re.search(r"\b(anxiety|anxious|nervous|scared|panic|worried|fear|tensed|stressed)\b", text_lower):
            return "anxious", 0.86
        if re.search(r"\b(frustrated|angry|upset|irritated|annoyed|fed up)\b", text_lower):
            return "frustrated", 0.82
        if re.search(r"\b(sad|depressed|down|hopeless|tearful)\b", text_lower):
            return "sad", 0.75
        if re.search(r"\b(happy|good|fine|okay|better|relieved)\b", text_lower):
            return "positive", 0.72
        return "neutral", 0.56
