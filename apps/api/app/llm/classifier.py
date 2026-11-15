"""Ticket Classifier with Pydantic V2 schema validation and repair, plus cheap TF-IDF baseline."""
import json
import logging
import re
from typing import Optional

from pydantic import ValidationError
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from apps.api.app.llm.client import LLMClient
from apps.api.app.llm.schemas import ClassificationOutput

logger = logging.getLogger("helpdeskflow.classifier")


class TFIDFBaselineClassifier:
    """Fast, lightweight TF-IDF baseline classifier for comparison against LLM."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=1000)
        self.model = LogisticRegression(max_iter=500)
        self.is_trained = False

    def train(self, texts: list[str], labels: list[str]) -> None:
        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)
        self.is_trained = True

    def predict(self, text: str) -> str:
        if not self.is_trained:
            # Simple rule fallback if not trained
            t = text.lower()
            if "bill" in t or "bkash" in t:
                return "billing"
            if "refund" in t or "cancel" in t:
                return "policy"
            if "order" in t or "router" in t or "cat6" in t:
                return "order"
            if "legal" in t or "btrc" in t or "fraud" in t:
                return "escalation"
            return "technical"
        X = self.vectorizer.transform([text])
        return str(self.model.predict(X)[0])


class TicketClassifier:
    """Triage and classification agent using LLMClient with schema repair & validation."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.tfidf_baseline = TFIDFBaselineClassifier()

    def _repair_json(self, raw: str) -> str:
        """Strip markdown fences, trailing commas, or surrounding prose."""
        cleaned = raw.strip()
        # Remove markdown code blocks if any
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()

        # Find first { and last }
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start: end + 1]

        return cleaned

    def classify(self, text: str, max_repair_attempts: int = 2) -> ClassificationOutput:
        """Classify a support ticket into Category, Priority, Language, Sentiment, Confidence."""
        prompt = (
            f"You are a ticket triage engine for BengalNet & Bazar (ISP & E-commerce in Bangladesh).\n"
            f"Analyze the following customer support ticket and classify it into valid JSON matching the schema:\n\n"
            f"Ticket Text:\n\"\"\"{text}\"\"\"\n\n"
            f"Required JSON Fields:\n"
            f"- category: technical | billing | policy | order | escalation | security\n"
            f"- priority: low | medium | high | urgent\n"
            f"- language: en | bn | banglish\n"
            f"- sentiment: positive | neutral | negative | hostile\n"
            f"- confidence: float between 0.0 and 1.0\n"
            f"- summary: 1-sentence summary\n"
            f"- detected_customer_id: string e.g. 'CUST-1042' or null\n"
            f"- detected_order_id: string e.g. 'ORD-20150' or null\n"
            f"- requires_human_approval: boolean (true for legal, refunds, severe complaints, or confidence < 0.75)"
        )

        system_prompt = "You are an automated support classifier. Output strict JSON only without explanation."

        raw_output = self.llm.generate_json(
            prompt=prompt,
            system_instruction=system_prompt,
            schema_name="classification"
        )

        # Attempt parse & validation with repair
        for attempt in range(max_repair_attempts):
            try:
                repaired = self._repair_json(raw_output)
                data = json.loads(repaired)
                return ClassificationOutput.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Classification JSON validation error on attempt {attempt + 1}: {e}")
                # Re-ask LLM to fix malformed JSON
                repair_prompt = f"The following JSON was invalid. Fix and output strictly valid JSON:\n\n{raw_output}"
                raw_output = self.llm.generate_json(
                    prompt=repair_prompt,
                    system_instruction="Fix invalid JSON syntax and missing fields. Output JSON only.",
                    schema_name="classification"
                )

        # Fallback to deterministic rule-based object if LLM output fails completely
        baseline_cat = self.tfidf_baseline.predict(text)
        return ClassificationOutput(
            category=baseline_cat,  # type: ignore[arg-type]
            priority="medium",
            language="en",
            sentiment="neutral",
            confidence=0.70,
            summary="Auto-classified by fallback classifier",
            detected_customer_id=None,
            detected_order_id=None,
            requires_human_approval=True
        )
