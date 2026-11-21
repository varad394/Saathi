"""Agora RTC tokens + ConvoAI REST client.

Endpoints verified against docs.agora.io/en/api-reference/api-ref/conversational-ai (Nov 2026):
  POST /join, POST /agents/{id}/speak, POST /agents/{id}/update, POST /agents/{id}/leave,
  GET /agents/{id}, GET /agents/{id}/history.  Auth: Basic (customer ID:secret).
"""
import base64
import copy
import logging
import re
import time

import httpx

import config as C
import settings as S
from agora_token.RtcTokenBuilder2 import Role_Publisher, RtcTokenBuilder

log = logging.getLogger("agora")

BASE = f"https://api.agora.io/api/conversational-ai-agent/v2/projects/{C.AGORA_APP_ID}"
_AUTH = "Basic " + base64.b64encode(f"{C.AGORA_CUSTOMER_ID}:{C.AGORA_CUSTOMER_SECRET}".encode()).decode()
_http = httpx.AsyncClient(timeout=15, headers={"Authorization": _AUTH, "Content-Type": "application/json"})

TOKEN_TTL = 3600
SPEAK_LIMIT = 512  # bytes, per Agora speak API


def rtc_token(channel: str, uid: int) -> str:
    return RtcTokenBuilder.build_token_with_uid(
        C.AGORA_APP_ID, C.AGORA_APP_CERTIFICATE, channel, uid, Role_Publisher, TOKEN_TTL, TOKEN_TTL
    )


def join_payload(*, name: str, channel: str, agent_uid: int, user_uid: int, llm_url: str, system_prompt: str,
                 greeting: str, voice: str, locale: str, asr_lang: str = "unknown", idle_timeout: int = 120,
                 asr_vendor: str = "sarvam",
                 failure_message: str = "Please wait, help is being arranged.") -> dict:
    return {
        "name": name,
        "properties": {
            "channel": channel,
            "token": rtc_token(channel, agent_uid),
            "agent_rtc_uid": str(agent_uid),
            "remote_rtc_uids": [str(user_uid)],
            "idle_timeout": idle_timeout,
            "asr": asr_block(asr_vendor, asr_lang),
            "llm": {
                "url": llm_url,
                "api_key": C.CUSTOM_LLM_SHARED_KEY,
                "style": "openai",
                "system_messages": [{"role": "system", "content": system_prompt}],
                "greeting_message": greeting,
                "failure_message": failure_message,
                "max_history": 20,
                "params": {"model": C.LLM_MODEL},
            },
            # Voice activity detection: a higher speech_threshold ignores quieter, distant voices (room chatter).
            "turn_detection": {"mode": "default", "config": {
                "speech_threshold": S.get("speech_threshold"),
                "end_of_speech": {"mode": "vad", "vad_config": {"silence_duration_ms": S.get("silence_ms")}}}},
            "tts": {
                "vendor": "murf",
                "params": {"api_key": C.MURF_API_KEY, "voiceId": voice, "locale": locale,
                           "model": C.MURF_MODEL, "sample_rate": 24000},
            },
        },
    }


def asr_block(vendor: str, lang: str) -> dict:
    if vendor == "ares":  # Agora's built-in ASR: no vendor key; several languages as one comma-separated string
        return {"vendor": "ares", "language": S.get("ares_langs") if lang == "unknown" else lang}
    # Sarvam: "unknown" = automatic language detection (scene); a fixed code for family / 112
    return {"vendor": "sarvam", "language": "en-IN" if lang == "unknown" else lang,
            "params": {"api_key": C.SARVAM_API_KEY, "language": lang}}


def _redact(p: dict) -> dict:
    q = copy.deepcopy(p)
    pr = q["properties"]
    pr["token"] = "<redacted>"
    if "params" in pr["asr"]:
        pr["asr"]["params"]["api_key"] = "<redacted>"
    pr["llm"]["api_key"] = "<redacted>"
    pr["tts"]["params"]["api_key"] = "<redacted>"
    pr["llm"]["system_messages"] = "<prompt>"
    return q


async def _post(path: str, body: dict | None = None) -> dict:
    t = time.perf_counter()
    r = await _http.post(BASE + path, json=body or {})
    log.info("POST %s -> %s in %.0f ms", path, r.status_code, (time.perf_counter() - t) * 1000)
    if r.status_code >= 300:
        log.error("Agora error body: %s", r.text[:500])
        raise httpx.HTTPStatusError(f"{r.status_code}: {r.text[:300]}", request=r.request, response=r)
    return r.json() if r.content else {}


async def join(**kw) -> dict:
    p = join_payload(**kw)
    log.info("join %s: %s", kw["name"], _redact(p))
    return await _post("/join", p)


def split_for_speak(text: str, limit: int = SPEAK_LIMIT - 12) -> list[str]:
    """Split text into chunks under the speak byte limit, preferring sentence boundaries."""
    text = text.strip()
    if len(text.encode("utf-8")) <= limit:
        return [text] if text else []
    parts = [p for p in re.split(r"(?<=[.!?।॥])\s+", text) if p]
    out, cur = [], ""
    for p in parts:
        cand = (cur + " " + p).strip()
        if len(cand.encode("utf-8")) <= limit:
            cur = cand
            continue
        if cur:
            out.append(cur)
        while len(p.encode("utf-8")) > limit:  # a single very long sentence: hard split on spaces
            words, piece = p.split(" "), ""
            for w in words:
                if len((piece + " " + w).encode("utf-8")) > limit:
                    break
                piece = (piece + " " + w).strip()
            out.append(piece)
            p = p[len(piece):].strip()
        cur = p
    if cur:
        out.append(cur)
    return out


async def speak(agent_id: str, text: str, priority: str = "APPEND", interruptable: bool = True) -> None:
    """Speak text word for word through Murf. Long text is split; later chunks always APPEND."""
    for i, chunk in enumerate(split_for_speak(text)):
        await _post(f"/agents/{agent_id}/speak", {
            "text": chunk, "priority": priority if i == 0 else "APPEND", "interruptable": interruptable})


async def leave(agent_id: str) -> dict:
    return await _post(f"/agents/{agent_id}/leave")


async def query(agent_id: str) -> dict:
    r = await _http.get(f"{BASE}/agents/{agent_id}")
    return {"http": r.status_code, **(r.json() if r.content else {})}


async def history(agent_id: str) -> dict:
    r = await _http.get(f"{BASE}/agents/{agent_id}/history")
    return {"http": r.status_code, **(r.json() if r.content else {})}
