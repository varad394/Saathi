"""Saathi backend. Run: .venv/Scripts/python -m uvicorn main:app --port 8000"""
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

import agora
import config as C
import protocol as P
import workflow as W
from crash import router as crash_router
from llm import router as llm_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s.%(msecs)03d %(name)s %(message)s", datefmt="%H:%M:%S")

app = FastAPI(title="Saathi")
app.include_router(llm_router, prefix="/llm")
app.include_router(crash_router)
STATIC = C.ROOT / "backend" / "static"


@app.get("/")
@app.get("/dash")
def dash():
    return FileResponse(STATIC / "dash.html")


@app.get("/j/{sid}")
def join_page(sid: str):
    return FileResponse(STATIC / "join.html")


@app.get("/health")
def health():
    return {"ok": True, "public_base_url": C.PUBLIC_BASE_URL or None, "incident": W.INC.id if W.INC else None,
            "state": W.INC.state if W.INC else None}


@app.get("/token")
def token(uid: int, channel: str):
    return {"app_id": C.AGORA_APP_ID, "channel": channel, "uid": uid, "token": agora.rtc_token(channel, uid)}


# ---- compatibility with the current Android app (Manual start / First-aid line / Stop buttons)
@app.post("/session/start")
async def session_start():
    from crash import simulate
    return await simulate()


@app.post("/session/speak")
async def session_speak():
    if not W.INC:
        raise HTTPException(409, "no incident")
    ids = await W.say_lines(["HELMET1"], critical=False) or ["HELMET1"]
    return {"ok": True, "text": P.text(ids[0], P.line_lang(W.INC.scene_lang))}


@app.post("/session/stop")
async def session_stop():
    if W.INC:
        await W.stop_all(W.INC)
        if W.INC.state not in ("CLOSED", "CANCELLED"):
            W.set_state("CLOSED", "stopped from the phone")
    return {"ok": True}
