"""OpenAI-compatible /llm/{sid}/chat/completions that Agora ConvoAI calls, one URL per agent session.

Per turn:
  1. Compact context: the role's system prompt + live STATUS (incident facts and the last few exchanges) +
     ONLY the latest message. The model never re-handles old turns, and each call stays small (rate limits).
  2. Tool loop with only the tools the current state allows (runs here, server-side).
  3. Reviewed protocol lines from a tool are spoken word for word via the speak API and the model's own text is
     dropped; a fixed line from a tool (rider check) is streamed back verbatim.
"""
import json
import logging
import re
import time
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

import config as C
import intent
import llmclient
import tools
import workflow as W

log = logging.getLogger("llm")
router = APIRouter()

MAX_ROUNDS = 3
FALLBACK = "Please wait, help is being arranged."
FALLBACK_BY_ROLE = {"ambulance": "Noted. I am checking with the people at the scene.",
                    "family": "मी त्यांच्याकडून माहिती घेत आहे, कृपया थांबा."}
_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]")


def _clean(text: str) -> str:
    """Spoken text only: drop emoji / markdown symbols, normalise odd spaces, keep it on one line."""
    text = _EMOJI.sub("", text).replace(" ", " ").replace(" ", " ")
    text = re.sub(r"[*_#`>]+", "", text)
    return re.sub(r"\s*\n+\s*", " ", text).strip()


def _chunk(cid: str, content: str | None = None, finish: str | None = None) -> str:
    delta = {"content": content} if content is not None else {}
    return "data: " + json.dumps({"id": cid, "object": "chat.completion.chunk", "created": int(time.time()),
                                  "model": C.LLM_MODEL, "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]},
                                 ensure_ascii=False) + "\n\n"


@router.post("/{sid}/chat/completions")
async def chat_completions(sid: str, req: Request):
    if req.headers.get("authorization", "") != f"Bearer {C.CUSTOM_LLM_SHARED_KEY}":
        raise HTTPException(401, "bad key")
    inc = W.INC
    s = inc.sessions.get(sid) if inc else None
    if s is None:
        raise HTTPException(404, "unknown or finished session")
    body = await req.json()
    msgs = body.get("messages", [])
    last_user = next((m.get("content") for m in reversed(msgs) if m.get("role") == "user"), "") or ""
    if isinstance(last_user, list):  # content parts
        last_user = " ".join(p.get("text", "") for p in last_user if isinstance(p, dict))
    engaged = W.on_utterance(s, last_user) if last_user else False

    messages = [{"role": "system", "content": s.system_prompt or W.SCENE_PROMPT},
                {"role": "system", "content": "STATUS:\n" + W.status_for(s)},
                {"role": "user", "content": last_user or "(silence)"}]
    tool_defs = tools.allowed(s)

    t0 = time.perf_counter()
    turn = {"lines": [], "critical": False, "say": None, "spoken": False}
    text, provider = "", "-"
    if s.role == "scene" and inc.state in ("IMPACT", "DETECTED", "RIDER_CHECK") and intent.rider_says_fine(last_user):
        turn["say"] = W.rider_status("ok", last_user).get("_say")  # C1: deterministic cancel, no LLM round
        provider = "intent"
    elif s.role == "scene" and inc.state in ("RIDER_CHECK", "CANCEL_PENDING", "CANCELLED") and intent.rider_needs_help(last_user):
        turn["say"] = W.rider_status("help", last_user).get("_say")  # C3 / changed his mind: escalate at once
        provider = "intent"
    try:
        for _ in range(0 if turn["say"] else MAX_ROUNDS):
            text, calls, provider = await llmclient.complete(messages, tool_defs, role=s.role, max_tokens=400)
            if not calls:
                break
            messages.append({"role": "assistant", "content": text or None, "tool_calls": [
                {"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": c["args"]}} for c in calls]})
            for c in calls:
                result = await tools.run(s, c["name"], c["args"], turn)
                log.info("TOOL [%s] %s(%s) -> %s", s.role, c["name"], c["args"], result)
                messages.append({"role": "tool", "tool_call_id": c["id"], "content": result})
            text = ""
            if turn["say"] or turn["lines"] or turn["spoken"]:
                break
    except Exception:
        log.exception("llm turn failed")

    out, lines = None, []
    if engaged:  # D5: Good Samaritan right after the first bystander reply, then assessment
        lines = (turn["lines"] + ["GS1"]) if turn["critical"] else (["GS1"] + (turn["lines"] or ["RESP1"]))
    elif turn["say"]:
        out = turn["say"]
    elif turn["lines"]:
        lines = turn["lines"]
    elif not turn["spoken"]:
        out = _clean(text)
        if not out or out.lstrip().startswith(("{", "[")):  # a model echoing a tool result: never speak JSON
            out = (FAMILY_WAIT.get(s.lang, FAMILY_WAIT["en"]) if s.role == "family"
                   else FALLBACK_BY_ROLE.get(s.role, FALLBACK))
    if out:
        W.ev("said", sid=s.sid, text=out)  # shown in the live transcript (phone + dashboard)
    if lines:
        W.spawn(W.say_lines(list(dict.fromkeys(lines)), critical=turn["critical"]))
    log.info("TURN [%s] via %s heard=%r -> %s (%.0f ms)", s.role, provider, last_user,
             f"say {out!r}" if out else f"lines {lines}" if lines else "spoken by tool", (time.perf_counter() - t0) * 1000)

    async def gen():
        cid = "chatcmpl-" + uuid.uuid4().hex[:12]
        if out:
            yield _chunk(cid, out)
        yield _chunk(cid, finish="stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
