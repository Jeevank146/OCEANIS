from abc import ABC, abstractmethod
import json
import logging
import os
import re
from typing import Any, Dict, Optional

logger = logging.getLogger("oceanis.conversation.llm")


class BaseLLMClient(ABC):
    """
    Abstract LLM Provider interface.
    Decouples OCEANIS conversational intelligence from specific LLM vendors.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.1,
    ) -> str:
        """
        Generates completion text or JSON string from the underlying LLM or rule engine.
        """
        pass


class DeterministicRuleLLMClient(BaseLLMClient):
    """
    High-performance deterministic rule-based fallback LLM client.
    Operates completely offline with 0 external network requests or API keys.
    Used when no external LLM key is configured, during automated test runs,
    or when low-latency edge deployment is active.
    """

    @property
    def provider_name(self) -> str:
        return "deterministic_rule_engine"

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.1,
    ) -> str:
        if json_mode:
            # Generate structured mock JSON response for parser
            return json.dumps({
                "status": "deterministic_fallback",
                "message": "Structured rule parsing used",
            })
        return "Deterministic rule-based response generated."


class OpenAICompatibleLLMClient(BaseLLMClient):
    """
    Client for OpenAI and OpenAI-compatible API providers (vLLM, Ollama, Azure OpenAI).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    @property
    def provider_name(self) -> str:
        return f"openai_compatible ({self.model})"

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.1,
    ) -> str:
        if not self.api_key:
            return DeterministicRuleLLMClient().generate_text(prompt, system_prompt, json_mode, temperature)

        try:
            import httpx

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            with httpx.Client(timeout=15.0) as client:
                res = client.post(f"{self.base_url.rstrip('/')}/chat/completions", json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"OpenAI LLM call failed, falling back to rule engine: {e}")
            return DeterministicRuleLLMClient().generate_text(prompt, system_prompt, json_mode, temperature)


class GeminiLLMClient(BaseLLMClient):
    """
    Client for Google Gemini API.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    @property
    def provider_name(self) -> str:
        return f"google_gemini ({self.model})"

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.1,
    ) -> str:
        if not self.api_key:
            return DeterministicRuleLLMClient().generate_text(prompt, system_prompt, json_mode, temperature)

        try:
            import httpx

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            contents = []
            if system_prompt:
                contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_prompt}"}]})
                contents.append({"role": "model", "parts": [{"text": "Understood. I will follow these instructions."}]})
            contents.append({"role": "user", "parts": [{"text": prompt}]})

            payload: Dict[str, Any] = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                },
            }
            if json_mode:
                payload["generationConfig"]["responseMimeType"] = "application/json"

            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logger.warning(f"Gemini LLM call failed, falling back to rule engine: {e}")
            return DeterministicRuleLLMClient().generate_text(prompt, system_prompt, json_mode, temperature)


class LLMClientFactory:
    """
    Factory for instantiating the appropriate LLM client based on environment configuration.
    """

    @classmethod
    def get_client(cls, provider: Optional[str] = None) -> BaseLLMClient:
        selected_provider = (provider or os.getenv("LLM_PROVIDER", "auto")).lower()

        if selected_provider == "deterministic":
            return DeterministicRuleLLMClient()

        if selected_provider in ("openai", "azure") or (selected_provider == "auto" and os.getenv("OPENAI_API_KEY")):
            if os.getenv("OPENAI_API_KEY"):
                return OpenAICompatibleLLMClient()

        if selected_provider in ("gemini", "google") or (selected_provider == "auto" and os.getenv("GEMINI_API_KEY")):
            if os.getenv("GEMINI_API_KEY"):
                return GeminiLLMClient()

        # Default fallback
        return DeterministicRuleLLMClient()
