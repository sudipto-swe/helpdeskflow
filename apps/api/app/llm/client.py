"""Unified LLMClient with disk caching, retry exponential backoff, request counters,
and support for providers: mock, gemini, groq, openrouter, ollama.
All unit tests and CI run deterministically on `mock` without network or API costs.
"""
import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Optional

import httpx

from apps.api.app.core.config import settings

logger = logging.getLogger("helpdeskflow.llm")


class LLMClient:
    """Unified LLM Client adhering to Section B Zero-Budget and Single Interface rules."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        cache_dir: Optional[str] = None
    ):
        self.provider = provider or settings.LLM_PROVIDER
        self.model = model or settings.LLM_MODEL
        self.cache_dir = Path(cache_dir or settings.LLM_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.request_count = 0
        self.cached_count = 0
        self.total_tokens_used = 0

    def _get_cache_key(self, prompt: str, schema_name: str) -> str:
        raw = f"{self.provider}:{self.model}:{schema_name}:{prompt}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _read_cache(self, cache_key: str) -> Optional[str]:
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.cached_count += 1
                    return data.get("response")
            except Exception as e:
                logger.warning(f"Failed to read LLM cache: {e}")
        return None

    def _write_cache(self, cache_key: str, response: str) -> None:
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({"response": response, "timestamp": time.time()}, f)
        except Exception as e:
            logger.warning(f"Failed to write LLM cache: {e}")

    def generate_json(
        self,
        prompt: str,
        system_instruction: str = "",
        schema_name: str = "default",
        max_retries: int = 3
    ) -> str:
        """Generate structured JSON with retry, backoff, and caching."""
        self.request_count += 1
        cache_key = self._get_cache_key(prompt + system_instruction, schema_name)
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached

        # Dispatch by provider with exponential backoff
        delay = 1.0
        last_exception = None

        for attempt in range(max_retries):
            try:
                if self.provider == "mock":
                    response = self._mock_generate(prompt, schema_name)
                elif self.provider == "gemini":
                    response = self._call_gemini(prompt, system_instruction)
                elif self.provider == "groq":
                    response = self._call_groq(prompt, system_instruction)
                elif self.provider == "openrouter":
                    response = self._call_openrouter(prompt, system_instruction)
                elif self.provider == "ollama":
                    response = self._call_ollama(prompt, system_instruction)
                else:
                    response = self._mock_generate(prompt, schema_name)

                # Estimate tokens
                tokens = (len(prompt) + len(response)) // 4
                self.total_tokens_used += tokens

                self._write_cache(cache_key, response)
                return response

            except Exception as e:
                last_exception = e
                logger.warning(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(delay)
                delay *= 2.0

        raise RuntimeError(f"LLM generate failed after {max_retries} attempts: {last_exception}")

    def _mock_generate(self, prompt: str, schema_name: str) -> str:
        """Deterministic mock provider producing schema-compliant JSON for testing & CI."""
        # Extract ticket body if wrapped in Ticket Text: """..."""
        target_text = prompt
        match = re.search(r'Ticket Text:\s*"""(.*?)"""', prompt, re.DOTALL)
        if match:
            target_text = match.group(1)

        lower = target_text.lower()

        # Classification Mock
        if schema_name == "classification":
            category = "technical"
            priority = "medium"
            sentiment = "neutral"
            lang = "en"
            requires_approval = False

            # Detect language
            if re.search(r"[\u0980-\u09FF]", prompt):
                lang = "bn"
            elif any(w in lower for w in ["choltesena", "kintu", "ekhon", "vul", "kivabe", "fokirni", "disi"]):
                lang = "banglish"

            # Detect category & sensitivity
            if any(w in lower for w in ["fraudulent", "btrc", "legal", "lawsuit", "churi", "idiot", "smash", "court"]):
                category = "escalation"
                priority = "urgent"
                sentiment = "hostile"
                requires_approval = True
            elif any(w in lower for w in ["ignore all previous", "superadmin", "system override", "database customer records", "leak"]):
                category = "security"
                priority = "urgent"
                sentiment = "hostile"
                requires_approval = True
            elif any(w in lower for w in ["red light", "los", "speed", "mbps", "buffer", "বাতি", "ওয়াইফাই", "router onu", "onu"]):
                category = "technical"
                priority = "high" if ("red" in lower or "los" in lower) else "medium"
            elif any(w in lower for w in ["bkash", "trxid", "bill", "invoice", "late fee", "বিল", "বিকাশ"]):
                category = "billing"
                priority = "medium"
            elif any(w in lower for w in ["refund", "downtime", "cancel", "return", "policy", "রিফান্ড"]):
                category = "policy"
                priority = "high"
                requires_approval = True
            elif any(w in lower for w in ["order", "cat6", "delivery", "parcel", "পার্সেল"]):
                category = "order"
                priority = "medium"

            # Extract IDs
            cust_match = re.search(r"CUST-\d+", prompt)
            cust_id = cust_match.group(0) if cust_match else None
            ord_match = re.search(r"ORD-\d+", prompt)
            ord_id = ord_match.group(0) if ord_match else None

            data = {
                "category": category,
                "priority": priority,
                "language": lang,
                "sentiment": sentiment,
                "confidence": 0.94,
                "summary": f"Customer reporting {category} issue.",
                "detected_customer_id": cust_id,
                "detected_order_id": ord_id,
                "requires_human_approval": requires_approval
            }
            return json.dumps(data)

        # Draft Mock
        elif schema_name == "draft":
            is_sensitive = any(w in lower for w in ["legal", "btrc", "fraudulent", "refund", "superadmin", "security"])
            citations = []
            if "KB-TEC-001" in prompt:
                citations.append("KB-TEC-001")
            elif "KB-POL-001" in prompt:
                citations.append("KB-POL-001")
            elif "KB-BIL-002" in prompt:
                citations.append("KB-BIL-002")

            reply = (
                "Hello, thank you for reaching out to BengalNet & Bazar support. "
                "We have logged your request. Based on our policy, our technical and support teams are actively "
                "addressing the issue. If you have an urgent inquiry, our helpline is always available."
            )
            return json.dumps({
                "reply_text": reply,
                "citations": citations,
                "action_taken": "search_kb",
                "confidence": 0.92,
                "requires_human_approval": is_sensitive,
                "approval_reason": "Sensitive category or policy requirement" if is_sensitive else None
            })

        # Generic JSON
        return json.dumps({"status": "ok", "provider": "mock", "prompt_len": len(prompt)})

    def _call_gemini(self, prompt: str, system_instruction: str) -> str:
        api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured in .env or environment")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]} if system_instruction else None,
            "generationConfig": {"responseMimeType": "application/json"}
        }
        with httpx.Client(timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    def _call_groq(self, prompt: str, system_instruction: str) -> str:
        api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError("GROQ_API_KEY not configured in .env")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_instruction or "Respond strictly with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        with httpx.Client(timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    def _call_openrouter(self, prompt: str, system_instruction: str) -> str:
        api_key = settings.OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {
            "model": "meta-llama/llama-3.1-8b-instruct:free",
            "messages": [
                {"role": "system", "content": system_instruction or "Respond strictly with valid JSON."},
                {"role": "user", "content": prompt}
            ]
        }
        with httpx.Client(timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    def _call_ollama(self, prompt: str, system_instruction: str) -> str:
        base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        url = f"{base_url}/api/chat"
        payload = {
            "model": "llama3",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "format": "json",
            "stream": False
        }
        with httpx.Client(timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()["message"]["content"]
