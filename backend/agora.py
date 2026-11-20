"""Agora RTC tokens + ConvoAI REST client (join / speak / update / leave / query).

Endpoints verified against docs.agora.io/en/api-reference/api-ref/conversational-ai (Nov 2026).
"""
import base64
import logging
import time

import httpx

import config as C
from agora_token.RtcTokenBuilder2 import Role_Publisher, RtcTokenBuilder

log = logging.getLogger("agora")

BASE = f"https://api.agora.io/api/conversational-ai-agent/v2/projects/{C.AGORA_APP_ID}"
_AUTH = "Basic " + base64.b64encode(f"{C.AGORA_CUSTOMER_ID}:{C.AGORA_CUSTOMER_SECRET}".encode()).decode()
_http = httpx.AsyncClient(timeout=15, headers={"Authorization": _AUTH, "Content-Type": "application/json"})

TOKEN_TTL = 3600


def rtc_token(channel: str, uid: int) -> str:
    return RtcTokenBuilder.build_token_with_uid(
        C.AGORA_APP_ID, C.AGORA_APP_CERTIFICATE, channel, uid, Role_Publisher, TOKEN_TTL, TOKEN_TTL
    )


SYSTEM_PROMPT = """You are Saathi, the voice of a two-wheeler rider's phone, speaking on loudspeaker right after a possible crash.
Rules:
- Reply in ONE short sentence (max 20 words). It will be spoken aloud.
- Reply in the same language the person just used: Kannada in Kannada script, Hindi in Devanagari, English in English. Code-mixed input: answer in the dominant language.
- When the rider says anything about how they are (fine, hurt, pain, help, cannot breathe), call log_rider_status first, then reply.
- To know who the rider is or where the crash is, call get_crash_context. Never say any phone number.
- Never invent medical advice. If asked what to do medically, say: "Please wait for the ambulance, help is being arranged."
- Never say the rider is fine or that it is serious. Say only what you know."""

GREETING = "Saathi here. Looks like you fell. Are you okay? ನೀವು ಸರಿ ಇದ್ದೀರಾ? क्या आप ठीक हैं?"


def asr_block(vendor: str) -> dict:
    if vendor == "ares":  # Agora built-in ASR, diagnostic only (English)
        return {"vendor": "ares", "language": "en-US"}
    return {"vendor": "sarvam", "language": "en-IN",
            "params": {"api_key": C.SARVAM_API_KEY, "language": "unknown"}}


def join_payload(channel: str, llm_url: str, asr_vendor: str = "sarvam") -> dict:
    return {
        "name": f"saathi-{int(time.time())}",
        "properties": {
            "channel": channel,
            "token": rtc_token(channel, C.AGENT_UID),
            "agent_rtc_uid": str(C.AGENT_UID),
            "remote_rtc_uids": [str(C.USER_UID)],
            "idle_timeout": 60,
            "asr": asr_block(asr_vendor),
            "llm": {
                "url": llm_url,
                "api_key": C.CUSTOM_LLM_SHARED_KEY,
                "style": "openai",
                "system_messages": [{"role": "system", "content": SYSTEM_PROMPT}],
                "greeting_message": GREETING,
                "failure_message": "Please wait, help is being arranged.",
                "max_history": 16,
                "params": {"model": C.LLM_MODEL},
            },
            "tts": {
                "vendor": "murf",
                "params": {
                    "api_key": C.MURF_API_KEY,
                    "voiceId": C.MURF_VOICE_ID,
                    "locale": "en-IN",
                    "model": C.MURF_MODEL,
                    "sample_rate": 24000,
                },
            },
        },
    }


def _redact(p: dict) -> dict:
    import copy

    q = copy.deepcopy(p)
    pr = q["properties"]
    pr["token"] = "<redacted>"
    if "params" in pr["asr"]:
        pr["asr"]["params"]["api_key"] = "<redacted>"
    pr["llm"]["api_key"] = "<redacted>"
    pr["tts"]["params"]["api_key"] = "<redacted>"
    return q


async def _post(path: str, body: dict | None = None) -> dict:
    t = time.perf_counter()
    r = await _http.post(BASE + path, json=body or {})
    ms = (time.perf_counter() - t) * 1000
    log.info("POST %s -> %s in %.0f ms", path, r.status_code, ms)
    if r.status_code >= 300:
        log.error("Agora error body: %s", r.text[:500])
        raise httpx.HTTPStatusError(f"{r.status_code}: {r.text[:300]}", request=r.request, response=r)
    return r.json() if r.content else {}


async def join(channel: str, llm_url: str, asr_vendor: str = "sarvam") -> dict:
    p = join_payload(channel, llm_url, asr_vendor)
    log.info("join payload: %s", _redact(p))
    return await _post("/join", p)


async def speak(agent_id: str, text: str, priority: str = "INTERRUPT", interruptable: bool = False) -> dict:
    if len(text.encode("utf-8")) > 512:
        raise ValueError(f"speak text is {len(text.encode('utf-8'))} bytes; Agora limit is 512")
    return await _post(f"/agents/{agent_id}/speak", {"text": text, "priority": priority, "interruptable": interruptable})


async def update_system(agent_id: str, extra_system: str) -> dict:
    # llm.params is replaced wholesale on update, so always resend it.
    return await _post(f"/agents/{agent_id}/update", {"properties": {"llm": {
        "system_messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "system", "content": extra_system}],
        "params": {"model": C.LLM_MODEL},
    }}})


async def leave(agent_id: str) -> dict:
    return await _post(f"/agents/{agent_id}/leave")


async def query(agent_id: str) -> dict:
    r = await _http.get(f"{BASE}/agents/{agent_id}")
    return {"http": r.status_code, **(r.json() if r.content else {})}


async def history(agent_id: str) -> dict:
    r = await _http.get(f"{BASE}/agents/{agent_id}/history")
    return {"http": r.status_code, **(r.json() if r.content else {})}
