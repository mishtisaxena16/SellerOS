"""
Reasoner — the one place an agent calls out to an LLM. Listed as a
BaseAgent component in section 14 alongside Planner/ToolManager/
ContextBuilder/PromptBuilder.

Why a Protocol + swappable client instead of hardcoding an API: this
matches the project's existing local-first setup — the Streamlit demo
apps built during the summer training run entirely on local Ollama
models (llama3.2:1b for text, per the "Recent months" project history)
because of hardware constraints, not cloud APIs. `OllamaReasoner`
below is the default implementation for that reason, but every
specialized agent talks to `LLMReasoner` (the Protocol), never to
Ollama specifically — swapping to a hosted model later means writing
one new class, not touching any agent.

Honest status: `OllamaReasoner.generate()` makes a real HTTP call to
`http://localhost:11434/api/generate` (Ollama's default local port) —
it is NOT mocked. It will only work when run on a machine with Ollama
actually running locally with the relevant model pulled, same as her
other local SellerOS components. In this sandbox there is no reachable
Ollama instance, so calling it here would just fail with a connection
error — that's expected, not a bug in this file.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional, Protocol

import urllib.request
import urllib.error


@dataclass
class ReasonerResult:
    text: str
    raw: Optional[dict[str, Any]] = None


class LLMReasoner(Protocol):
    async def generate(self, prompt: str, **kwargs: Any) -> ReasonerResult:
        ...


class OllamaReasoner:
    """Default local Reasoner backend, matching the Ollama-based stack
    already used across her Streamlit demo apps and the earlier
    Flask-based SellerOS copilot."""

    def __init__(self, model: str = "llama3.2:1b", host: str = "http://localhost:11434") -> None:
        self.model = model
        self.host = host.rstrip("/")

    async def generate(self, prompt: str, **kwargs: Any) -> ReasonerResult:
        import asyncio
        return await asyncio.to_thread(self._generate_sync, prompt, kwargs)

    def _generate_sync(self, prompt: str, options: dict[str, Any]) -> ReasonerResult:
        payload = {
            "model": options.get("model", self.model),
            "prompt": prompt,
            "stream": False,
        }
        if "temperature" in options:
            payload["options"] = {"temperature": options["temperature"]}

        request = urllib.request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=options.get("timeout", 60)) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ConnectionError(
                f"Could not reach Ollama at {self.host}. Is `ollama serve` running "
                f"locally with '{payload['model']}' pulled? Original error: {exc}"
            ) from exc

        return ReasonerResult(text=body.get("response", ""), raw=body)


class StaticReasoner:
    """Test/dev double that returns a fixed string instead of calling
    any model. Useful for unit-testing agents' plan/prompt wiring
    without needing Ollama running — NOT a substitute for the real
    thing in any agent's default configuration."""

    def __init__(self, fixed_response: str = "") -> None:
        self.fixed_response = fixed_response

    async def generate(self, prompt: str, **kwargs: Any) -> ReasonerResult:
        return ReasonerResult(text=self.fixed_response, raw={"prompt": prompt})
