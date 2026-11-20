"""OpenAI-compatible /chat/completions endpoint that Agora ConvoAI calls.

Pattern from Agora's recipe-agent-tool-calling: the tool loop runs here, server-side,
and only final spoken text is streamed back to Agora as SSE. Reasoning tokens from
gpt-oss (delta.reasoning) are never forwarded, so they can't be spoken.
"""
import json
import logging
import time
import uuid

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

import config as C
from tools import TOOLS, event, run_tool

log = logging.getLogger("llm")
router = APIRouter()
_http = httpx.AsyncClient(timeout=httpx.Timeout(30, connect=5),
                          headers={"Authorization": f"Bearer {C.LLM_API_KEY}"})

MAX_ROUNDS = 3
FALLBACK = "Please wait, help is being arranged."
_KEEP = {"role", "content", "tool_calls", "tool_call_id", "name"}


def _sanitize(messages: list[dict]) -> list[dict]:
    out = []
    for m in messages:
        m = {k: v for k, v in m.items() if k in _KEEP}
        if m.get("role") in ("system", "user", "assistant", "tool"):
            out.append(m)
    return out


def _chunk(cid: str, content: str | None = None, finish: str | None = None) -> str:
    delta = {"content": content} if content is not None else {}
    return "data: " + json.dumps({
        "id": cid, "object": "chat.completion.chunk", "created": int(time.time()), "model": C.LLM_MODEL,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
    }, ensure_ascii=False) + "\n\n"


@router.post("/chat/completions")
async def chat_completions(req: Request):
    if req.headers.get("authorization", "") != f"Bearer {C.CUSTOM_LLM_SHARED_KEY}":
        raise HTTPException(401, "bad key")
    body = await req.json()
    messages = _sanitize(body.get("messages", []))
    last_user = next((m.get("content") for m in reversed(messages) if m.get("role") == "user"), None)
    log.info("ASR heard: %r", last_user)
    if last_user:
        event("heard", text=last_user)

    async def gen():
        cid = "chatcmpl-" + uuid.uuid4().hex[:12]
        t0 = time.perf_counter()
        first_token_ms = None
        spoken = ""
        try:
            for rnd in range(MAX_ROUNDS):
                payload = {"model": C.LLM_MODEL, "messages": messages, "tools": TOOLS, "tool_choice": "auto",
                           "stream": True, "max_tokens": 300, "reasoning_effort": "low"}
                calls: dict[int, dict] = {}
                text = ""
                async with _http.stream("POST", f"{C.LLM_BASE_URL}/chat/completions", json=payload) as r:
                    if r.status_code != 200:
                        log.error("upstream %s: %s", r.status_code, (await r.aread())[:300])
                        break
                    async for line in r.aiter_lines():
                        if not line.startswith("data:") or line.strip() == "data: [DONE]":
                            continue
                        choices = json.loads(line[5:]).get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta") or {}
                        if delta.get("content"):
                            if first_token_ms is None:
                                first_token_ms = (time.perf_counter() - t0) * 1000
                            text += delta["content"]
                            yield _chunk(cid, delta["content"])
                        for tc in delta.get("tool_calls") or []:
                            c = calls.setdefault(tc.get("index", 0), {"id": "", "name": "", "args": ""})
                            c["id"] = tc.get("id") or c["id"]
                            f = tc.get("function") or {}
                            c["name"] += f.get("name") or ""
                            c["args"] += f.get("arguments") or ""
                spoken += text
                if not calls:
                    break
                messages.append({"role": "assistant", "content": text or None, "tool_calls": [
                    {"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": c["args"]}}
                    for c in calls.values()]})
                for c in calls.values():
                    result = run_tool(c["name"], c["args"])
                    log.info("TOOL %s(%s) -> %s [round %d]", c["name"], c["args"], result, rnd)
                    messages.append({"role": "tool", "tool_call_id": c["id"], "content": result})
        except Exception:
            log.exception("llm loop failed")
        if not spoken.strip():
            spoken = FALLBACK
            yield _chunk(cid, FALLBACK)
        log.info("SAID %r (first token %s ms, total %.0f ms)", spoken,
                 f"{first_token_ms:.0f}" if first_token_ms else "-", (time.perf_counter() - t0) * 1000)
        event("said", text=spoken)
        yield _chunk(cid, finish="stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
