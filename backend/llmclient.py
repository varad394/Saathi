"""One LLM client for every caller, with a provider fallback chain.

Groq's free tier limits each model separately (8K tokens/min for gpt-oss-120b), so roles start on different
models and fall through to the next on 429 / 5xx / timeout. A model that returns 429 is skipped until its
cooldown ends. Sarvam-105B (OpenAI-compatible, same key as Sarvam ASR) is the last resort: slower, but strong
on Indian languages and parallel tool calls.
"""
import logging
import time
from dataclasses import dataclass

import httpx

import config as C
import settings as S

log = logging.getLogger("llmclient")


@dataclass(frozen=True)
class Provider:
    name: str
    base: str
    key: str
    model: str
    reasoning: bool  # accepts reasoning_effort
    timeout: float


def _groq(tag: str, model: str) -> list[Provider]:
    return [Provider(f"groq-{tag}-{i + 1}", C.LLM_BASE_URL, k, model, True, 10) for i, k in enumerate(C.LLM_API_KEYS)]


# Every selectable model -> its providers (several Groq keys rotate round-robin). Empty if no key is configured.
MODELS = {
    "groq-120b": _groq("main", C.LLM_MODEL),
    "groq-20b": _groq("fast", C.LLM_FAST_MODEL),
    "gpt-4o": [Provider("openai-4o", "https://api.openai.com/v1", C.OPENAI_API_KEY, "gpt-4o", False, 12)] if C.OPENAI_API_KEY else [],
    "gpt-4o-mini": [Provider("openai-4o-mini", "https://api.openai.com/v1", C.OPENAI_API_KEY, "gpt-4o-mini", False, 12)] if C.OPENAI_API_KEY else [],
    "sarvam-105b": [Provider("sarvam", "https://api.sarvam.ai/v2", C.SARVAM_API_KEY, C.SARVAM_LLM_MODEL, False, 20)],
}
FALLBACK_ORDER = ["groq-120b", "groq-20b", "gpt-4o-mini", "gpt-4o", "sarvam-105b"]
_rr = 0


def _chain(role: str) -> list[Provider]:
    """The model chosen in settings first (scene_llm for the scene, helper_llm for family/112/translation),
    then every other configured model as fallback. Keys of one model rotate round-robin."""
    global _rr
    _rr += 1
    first = S.get("scene_llm") if role == "scene" else S.get("helper_llm")
    if not MODELS.get(first):
        log.warning("LLM %s selected but not configured (missing key?) - using fallbacks", first)
    out = []
    for name in [first] + [m for m in FALLBACK_ORDER if m != first]:
        tier = MODELS.get(name) or []
        if tier:
            k = _rr % len(tier)
            out += tier[k:] + tier[:k]
    return out


_http = httpx.AsyncClient(timeout=httpx.Timeout(20, connect=5))
_cooldown: dict[str, float] = {}


async def complete(messages: list[dict], tools: list[dict] | None = None, role: str = "scene",
                   max_tokens: int = 400) -> tuple[str, list[dict], str]:
    """Returns (text, tool_calls[{id,name,args}], provider_name)."""
    last_err = "no provider"
    for p in _chain(role):
        if time.time() < _cooldown.get(p.name, 0):
            continue
        body = {"model": p.model, "messages": messages, "max_tokens": max_tokens}
        if p.reasoning:
            body["reasoning_effort"] = "low"
        if tools:
            body |= {"tools": tools, "tool_choice": "auto"}
        t = time.perf_counter()
        try:
            r = await _http.post(f"{p.base}/chat/completions", json=body, timeout=p.timeout, headers={
                "Authorization": f"Bearer {p.key}", **({"api-subscription-key": p.key} if p.name == "sarvam" else {})})
        except httpx.HTTPError as e:
            last_err = f"{p.name}: {type(e).__name__}"
            log.warning("LLM %s failed: %s", p.name, last_err)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            wait = float(r.headers.get("retry-after", 0) or 0) or 20
            _cooldown[p.name] = time.time() + min(wait, 60)
            last_err = f"{p.name}: HTTP {r.status_code}"
            log.warning("LLM %s -> %s; cooling down %.0f s", p.name, r.status_code, min(wait, 60))
            continue
        if r.status_code != 200:
            last_err = f"{p.name}: HTTP {r.status_code} {r.text[:200]}"
            log.error("LLM %s", last_err)
            continue
        m = r.json()["choices"][0]["message"]
        calls = [{"id": c.get("id", ""), "name": c["function"]["name"], "args": c["function"].get("arguments") or "{}"}
                 for c in (m.get("tool_calls") or [])]
        log.info("LLM %s (%s) %.0f ms, %d tool call(s), tokens left %s", p.name, role, (time.perf_counter() - t) * 1000,
                 len(calls), r.headers.get("x-ratelimit-remaining-tokens", "?"))
        return (m.get("content") or "").strip(), calls, p.name
    raise RuntimeError(f"all LLM providers failed ({last_err})")
