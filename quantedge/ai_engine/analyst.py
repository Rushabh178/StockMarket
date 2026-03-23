"""Provider-based analyst helpers for trade summaries and sentiment."""

from __future__ import annotations

import json
import logging
from typing import Any

from ..config import (
    AI_PROVIDER,
    GROQ_API_KEY,
    GROQ_MODEL,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
)

logger = logging.getLogger(__name__)

try:
    from groq import Groq
except ImportError:  # pragma: no cover - runtime safety only
    Groq = None

try:
    import anthropic
except ImportError:  # pragma: no cover - runtime safety only
    anthropic = None


def _get_provider_and_client() -> tuple[str, Any | None]:
    """Create provider client based on AI_PROVIDER."""
    provider = AI_PROVIDER if AI_PROVIDER in {"groq", "anthropic"} else "groq"

    if provider == "anthropic":
        if not ANTHROPIC_API_KEY:
            return provider, None
        if anthropic is None:
            logger.warning("anthropic package is not installed; Claude features are disabled.")
            return provider, None
        return provider, anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    if not GROQ_API_KEY:
        return provider, None
    if Groq is None:
        logger.warning("groq package is not installed; Groq features are disabled.")
        return provider, None
    return provider, Groq(api_key=GROQ_API_KEY)


def _chat_completion(prompt: str, max_tokens: int = 220, temperature: float = 0.2) -> str:
    """Run a single chat completion against configured provider."""
    provider, client = _get_provider_and_client()
    if client is None:
        raise RuntimeError(f"AI provider '{provider}' is not configured")

    if provider == "anthropic":
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        content = ""
        if response.content:
            for part in response.content:
                text = getattr(part, "text", "")
                if text:
                    content += text
        return content.strip()

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.choices[0].message.content
    return content.strip() if content else ""


def generate_trade_brief(screen_result: dict) -> str:
    """Generate a concise trade brief from screen output."""
    payload = {
        "symbol": screen_result.get("symbol"),
        "sector": screen_result.get("sector"),
        "composite_score": screen_result.get("composite_score"),
        "technical_score": screen_result.get("technical_score"),
        "fundamental_score": screen_result.get("fundamental_score"),
        "is_multibagger": screen_result.get("is_multibagger"),
        "rsi": screen_result.get("rsi"),
        "volume_ratio": screen_result.get("volume_ratio"),
        "current_price": screen_result.get("current_price"),
        "stop_loss": screen_result.get("stop_loss"),
        "target": screen_result.get("target"),
        "rules_passed": [
            k
            for k, v in screen_result.get("technical_details", {}).items()
            if isinstance(v, dict) and v.get("passed")
        ],
        "fundamentals": screen_result.get("fundamental_details", {}),
    }

    prompt = f"""
You are a senior equity analyst at a Mumbai-based hedge fund.

A stock screener has flagged this stock. Analyse the data and write
a concise swing trade brief in exactly this format - no extra text:

SETUP: <1 sentence describing the technical setup>
EDGE: <1 sentence on what makes this interesting right now>
RISK: <1 sentence on the biggest risk to this trade>
VERDICT: <BUY ZONE / WAIT / AVOID> - <5 words max reason>

Stock data:
{json.dumps(payload, indent=2)}

Rules that passed: {payload['rules_passed']}
Be specific to THIS stock. No generic advice.
"""

    return _chat_completion(prompt=prompt, max_tokens=220, temperature=0.2)


def analyze_news_sentiment(symbol: str, headlines: list[str]) -> dict:
    """Score headlines into structured sentiment JSON."""
    if not headlines:
        return {
            "sentiment_score": 0,
            "label": "NEUTRAL",
            "key_risk": "No headlines available",
            "key_catalyst": "No headlines available",
            "summary": "No headlines available",
        }

    prompt = f"""
Analyze these news headlines for {symbol} (Indian stock market).

Headlines:
{chr(10).join(f'- {h}' for h in headlines[:10])}

Respond ONLY in valid JSON, no other text:
{{
    "sentiment_score": <integer -10 to +10>,
    "label": "<BULLISH|BEARISH|NEUTRAL>",
    "key_risk": "<one short sentence>",
    "key_catalyst": "<one short sentence>",
    "summary": "<two sentences max>"
}}
"""

    text = _chat_completion(prompt=prompt, max_tokens=260, temperature=0.1)
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def explain_score_drop(
    symbol: str,
    prev_score: float,
    curr_score: float,
    prev_data: dict,
    curr_data: dict,
) -> str:
    """Explain material day-over-day score movement."""
    prompt = f"""
{symbol}'s composite score changed from {prev_score:.1f} to {curr_score:.1f}.

Previous indicators: {json.dumps(prev_data)}
Current indicators:  {json.dumps(curr_data)}

In 2 sentences: what changed technically and what does it mean
for a swing trader holding or watching this stock?
"""

    return _chat_completion(prompt=prompt, max_tokens=160, temperature=0.2)
