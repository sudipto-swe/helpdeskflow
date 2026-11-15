"""Fake delivery providers for notification and escalation logging."""
import logging
from typing import Any, Dict

logger = logging.getLogger("helpdeskflow.providers")


class FakeEmailProvider:
    """Mock Email delivery service for automated support responses."""

    def __init__(self):
        self.sent_emails: list[Dict[str, Any]] = []

    def send_email(self, to_email: str, subject: str, body: str) -> Dict[str, Any]:
        payload = {
            "to": to_email,
            "subject": subject,
            "body": body,
            "status": "delivered"
        }
        self.sent_emails.append(payload)
        logger.info(f"[FakeEmail] Delivered to {to_email}: {subject}")
        return payload


class FakeSlackProvider:
    """Mock Slack webhook delivery service for team escalation alerts."""

    def __init__(self):
        self.posted_messages: list[Dict[str, Any]] = []

    def post_alert(self, channel: str, message: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "channel": channel,
            "message": message,
            "metadata": metadata,
            "status": "posted"
        }
        self.posted_messages.append(payload)
        logger.info(f"[FakeSlack] Alert sent to #{channel}: {message}")
        return payload


fake_email = FakeEmailProvider()
fake_slack = FakeSlackProvider()
