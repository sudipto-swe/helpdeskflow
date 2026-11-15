"""Unit tests for Classifier with schema validation, repair, and mock LLM."""
import pytest

from apps.api.app.llm.classifier import TFIDFBaselineClassifier, TicketClassifier
from apps.api.app.llm.client import LLMClient
from apps.api.app.llm.schemas import ClassificationOutput


@pytest.fixture
def classifier():
    client = LLMClient(provider="mock")
    return TicketClassifier(llm_client=client)


def test_classify_technical_los(classifier):
    text = "The router ONU has red light blinking on LOS. Please fix."
    result = classifier.classify(text)
    assert isinstance(result, ClassificationOutput)
    assert result.category == "technical"
    assert result.priority in ["medium", "high", "urgent"]
    assert result.confidence >= 0.70
    assert result.language == "en"


def test_classify_bangla_billing(classifier):
    text = "আমি ২০ মিনিট আগে বিকাশ দিয়ে বিল দিয়েছি কিন্তু এখনও লাইন বন্ধ আছে। TrxID 9K8L23NM।"
    result = classifier.classify(text)
    assert isinstance(result, ClassificationOutput)
    assert result.category == "billing"
    assert result.language == "bn"


def test_classify_escalation_legal(classifier):
    text = "Your service is totally fraudulent! Overcharging me. I will complain to BTRC and file a lawsuit!"
    result = classifier.classify(text)
    assert isinstance(result, ClassificationOutput)
    assert result.category == "escalation"
    assert result.requires_human_approval is True
    assert result.sentiment == "hostile"


def test_json_repair_with_markdown_fences(classifier):
    raw_markdown = '```json\n{"category": "order", "priority": "low", "language": "en", "sentiment": "neutral", "confidence": 0.85, "summary": "Order query", "requires_human_approval": false}\n```'
    repaired = classifier._repair_json(raw_markdown)
    assert not repaired.startswith("```")
    assert repaired.endswith("}")


def test_tfidf_baseline():
    baseline = TFIDFBaselineClassifier()
    texts = [
        "red light on router onu",
        "paid bkash bill invoice late fee",
        "order delayed parcel router cat6",
        "btrc lawsuit fraud case escalation",
        "refund downtime policy cancellation"
    ]
    labels = ["technical", "billing", "order", "escalation", "policy"]
    baseline.train(texts, labels)

    pred = baseline.predict("red light blinking")
    assert pred == "technical"
    pred_bill = baseline.predict("bill payment via bkash")
    assert pred_bill == "billing"
