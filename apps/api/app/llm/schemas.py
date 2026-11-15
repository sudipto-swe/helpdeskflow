"""Pydantic V2 Schemas for ticket classification, extraction, and responses."""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

TicketCategory = Literal[
    "technical",
    "billing",
    "policy",
    "order",
    "escalation",
    "security"
]

TicketPriority = Literal[
    "low",
    "medium",
    "high",
    "urgent"
]

TicketLanguage = Literal[
    "en",
    "bn",
    "banglish"
]

TicketSentiment = Literal[
    "positive",
    "neutral",
    "negative",
    "hostile"
]


class ClassificationOutput(BaseModel):
    """Structured JSON schema for LLM ticket triage."""
    category: TicketCategory = Field(description="Operational category of the ticket")
    priority: TicketPriority = Field(description="Urgency and impact of the ticket")
    language: TicketLanguage = Field(description="Detected language of customer input")
    sentiment: TicketSentiment = Field(description="Customer sentiment level")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    summary: str = Field(description="1-sentence summary of customer inquiry")
    detected_customer_id: Optional[str] = Field(default=None, description="Customer ID if present in text")
    detected_order_id: Optional[str] = Field(default=None, description="Order ID if present in text")
    requires_human_approval: bool = Field(default=False, description="Flag for sensitive issues or low confidence")


class DraftResponseOutput(BaseModel):
    """Structured response draft produced by the workflow agent."""
    reply_text: str = Field(description="Empathetic, grounded response addressed to the customer")
    citations: List[str] = Field(default_factory=list, description="IDs of cited KB documents")
    action_taken: str = Field(description="Tool or action taken, e.g. search_kb, check_refund_policy")
    confidence: float = Field(ge=0.0, le=1.0)
    requires_human_approval: bool = Field(default=False)
    approval_reason: Optional[str] = Field(default=None)
