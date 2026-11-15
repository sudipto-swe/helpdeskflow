"""Safety Guardrails: PII masking, Prompt Injection Defense, Cross-Customer Isolation, and Budget Guards."""
import re
from typing import Tuple


class SafetyGuardrails:
    """Enterprise guardrails protecting against prompt injection, data leakage, and budget overflows."""

    # PII Regex patterns for Bangladesh and generic contact data
    PHONE_REGEX = re.compile(r"(?:\+880|880|01)[3-9]\d{8}\b")
    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
    CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
    NID_REGEX = re.compile(r"\b(?:NID:?\s*|nid:?\s*)(\d{10}|\d{13}|\d{17})\b", re.IGNORECASE)

    # Prompt Injection & Jailbreak Signatures
    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous\s+)?instructions", re.IGNORECASE),
        re.compile(r"system\s+override", re.IGNORECASE),
        re.compile(r"superadmin\s+god\s+mode", re.IGNORECASE),
        re.compile(r"repeat\s+verbatim", re.IGNORECASE),
        re.compile(r"output\s+all\s+database", re.IGNORECASE),
        re.compile(r"secret\s+key", re.IGNORECASE),
        re.compile(r"merchant\s+token", re.IGNORECASE),
        re.compile(r"print\s+['\"]ACCESS\s+GRANTED", re.IGNORECASE),
        re.compile(r"intercept\s+and\s+tap", re.IGNORECASE),
        re.compile(r"```json\s*\{\s*\"override\"", re.IGNORECASE),
        re.compile(r"give\s+me\s+a\s+list\s+of\s+all\s+customers", re.IGNORECASE),
        re.compile(r"change\s+the\s+registered\s+phone", re.IGNORECASE),
        re.compile(r"terminate\s+their\s+active\s+subscription", re.IGNORECASE),
        re.compile(r"free\s+\d+\s+months?\s+internet", re.IGNORECASE)
    ]

    @classmethod
    def mask_pii(cls, text: str) -> str:
        """Mask sensitive personally identifiable information (PII) before logging or sending to models."""
        masked = cls.PHONE_REGEX.sub("[PHONE_REDACTED]", text)
        masked = cls.EMAIL_REGEX.sub("[EMAIL_REDACTED]", masked)
        masked = cls.CREDIT_CARD_REGEX.sub("[CARD_REDACTED]", masked)
        masked = cls.NID_REGEX.sub("NID: [NID_REDACTED]", masked)
        return masked

    @classmethod
    def detect_prompt_injection(cls, text: str) -> Tuple[bool, str]:
        """Detect prompt injection, system override attempts, or exfiltration probes."""
        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(text):
                return True, f"Prompt injection pattern detected: {pattern.pattern}"
        return False, ""

    @classmethod
    def check_tool_budget(cls, tool_call_count: int, max_allowed: int = 5) -> bool:
        """Enforce strict per-ticket tool execution budget."""
        return tool_call_count < max_allowed

    @classmethod
    def verify_customer_isolation(
        cls,
        authenticated_customer_id: str,
        requested_customer_id: str
    ) -> bool:
        """Prevent cross-customer data access."""
        if not authenticated_customer_id or not requested_customer_id:
            return False
        return authenticated_customer_id.strip() == requested_customer_id.strip()
