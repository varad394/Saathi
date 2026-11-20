"""Saathi barebones backend. Run: .venv/Scripts/uvicorn main:app --port 8000"""
import logging
import time

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import agora
import config as C
import tools
from crash import router as crash_router
from llm import router as llm_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s.%(msecs)03d %(name)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("main")

app = FastAPI(title="Saathi barebones")
app.include_router(llm_router, prefix="/llm")
app.include_router(crash_router)

FIRST_AID_TEST_LINE = ("Do not remove his helmet. Do not move his neck. "
                       "ಹೆಲ್ಮೆಟ್ ತೆಗೆಯಬೇಡಿ. कृपया हेलमेट मत उतारिए।")


@app.get("/")
def index():
    return FileResponse(C.ROOT / "backend" / "static" / "index.html")


@app.get("/health")
def health():
    return {"ok": True, "public_base_url": C.PUBLIC_BASE_URL or None, "agent_id": tools.SESSION["agent_id"]}


@app.get("/token")
def token(uid: int = C.USER_UID, channel: str = C.CHANNEL):
    return {"app_id": C.AGORA_APP_ID, "channel": channel, "uid": uid, "token": agora.rtc_token(channel, uid)}


@app.post("/session/start")
async def session_start(asr: str = "sarvam"):
    return await start_agent(reason="manual", asr=asr)


async def start_agent(reason: str, asr: str = "sarvam", **data):
    if not C.PUBLIC_BASE_URL:
        raise HTTPException(400, "PUBLIC_BASE_URL is empty: start the tunnel and set it in .env")
    if tools.SESSION["agent_id"]:
        try:
            await agora.leave(tools.SESSION["agent_id"])
        except Exception:
            pass
    loc = tools.SESSION.get("location")
    tools.SESSION.update(agent_id=None, started_at=time.time(), timeline=[], location=loc)
    tools.event("start_requested", reason=reason, asr=asr, **data)
    try:
        res = await agora.join(C.CHANNEL, f"{C.PUBLIC_BASE_URL}/llm/chat/completions", asr)
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, f"Agora join failed: {e}")
    tools.SESSION["agent_id"] = res.get("agent_id")
    tools.event("agent_joined", agent_id=res.get("agent_id"), status=res.get("status"))
    # Everything the phone needs to join, in one response.
    return {**res, **token(C.USER_UID, C.CHANNEL)}


class SpeakIn(BaseModel):
    text: str | None = None
    priority: str = "INTERRUPT"
    interruptable: bool = False


@app.post("/session/speak")
async def session_speak(body: SpeakIn):
    aid = _agent()
    text = body.text or FIRST_AID_TEST_LINE
    try:
        await agora.speak(aid, text, body.priority, body.interruptable)
    except (ValueError, httpx.HTTPStatusError) as e:
        raise HTTPException(400, str(e))
    tools.event("speak", text=text)
    return {"ok": True, "text": text, "bytes": len(text.encode())}


@app.post("/session/stop")
async def session_stop():
    aid = _agent()
    try:
        await agora.leave(aid)
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, str(e))
    tools.event("stopped")
    tools.SESSION["agent_id"] = None
    return {"ok": True}


@app.get("/session/status")
async def session_status():
    aid = tools.SESSION["agent_id"]
    return {"agent": await agora.query(aid) if aid else None, "timeline": tools.SESSION["timeline"],
            "agora_history": (await agora.history(aid)).get("contents") if aid else None}


def _agent() -> str:
    if not tools.SESSION["agent_id"]:
        raise HTTPException(409, "no running agent; call /session/start")
    return tools.SESSION["agent_id"]
