"""Crash lifecycle + incident API. Detection runs on the phone; only these events come here.

  POST /crash/impact     -> pre-warm the scene agent (returns what the phone needs to join)
  POST /crash/confirmed  -> DETECTED -> RIDER_CHECK (20 s timer starts)
  POST /crash/cancel     -> detector false alarm before confirmation
  POST /crash/simulate   -> impact + confirmed in one call (testing without the phone's sensors)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import agora
import config as C
import settings as S
import workflow as W

router = APIRouter()


class ImpactIn(BaseModel):
    peak_g: float
    lat: float | None = None
    lon: float | None = None
    speed_kmh: float | None = None


class ConfirmIn(BaseModel):
    peak_g: float
    angle_deg: float
    still_std_g: float


class CancelIn(BaseModel):
    reason: str


@router.post("/crash/impact")
async def impact(body: ImpactIn):
    if not C.PUBLIC_BASE_URL:
        raise HTTPException(400, "PUBLIC_BASE_URL is empty: start the tunnel and set it in .env")
    return await W.on_impact(body.peak_g, body.lat, body.lon, body.speed_kmh)


@router.post("/crash/confirmed")
async def confirmed(body: ConfirmIn):
    await W.on_confirmed(body.peak_g, body.angle_deg, body.still_std_g)
    return {"ok": True, "state": W.INC.state if W.INC else None}


@router.post("/crash/cancel")
async def cancel(body: CancelIn):
    await W.on_detector_cancel(body.reason)
    return {"ok": True}


@router.post("/crash/rider_ok")
async def rider_ok():
    """The big I'M OK button on the phone (C2): same as the rider saying he is fine."""
    if not W.INC:
        raise HTTPException(409, "no incident")
    r = W.rider_status("ok", "(tapped I'M OK on the phone)")
    if r.get("_say"):
        W.spawn(W.say(W.INC.scene(), r["_say"], priority="INTERRUPT"))
    return {"state": W.INC.state}


@router.post("/crash/rider_help")
async def rider_help():
    """The I NEED HELP button: escalate at once."""
    if not W.INC:
        raise HTTPException(409, "no incident")
    r = W.rider_status("help", "(tapped I NEED HELP on the phone)")
    if r.get("_say"):
        W.spawn(W.say(W.INC.scene(), r["_say"], priority="INTERRUPT"))
    return {"state": W.INC.state}


@router.post("/crash/simulate")
async def simulate(peak_g: float = 4.0, asr: str | None = None):
    if not C.PUBLIC_BASE_URL:
        raise HTTPException(400, "PUBLIC_BASE_URL is empty: start the tunnel and set it in .env")
    res = await W.on_impact(peak_g, asr_vendor=asr if asr in ("sarvam", "ares") else None)
    res["mic"] = {"aec": S.get("mic_aec"), "ans": S.get("mic_ans"), "agc": S.get("mic_agc")}
    await W.on_confirmed(peak_g, 110.0, 0.05)
    return res


# ---------------------------------------------------------------- runtime settings (dashboard / phone app)
@router.get("/settings")
def get_settings():
    return S.all_()


@router.post("/settings")
def set_settings(patch: dict):
    return S.update(patch)


@router.post("/settings/reset")
def reset_settings():
    return S.reset()


# ---------------------------------------------------------------- incident (dashboard, follow-up)
@router.get("/incident")
def incident():
    return W.INC.public() if W.INC else {"state": "NONE"}


@router.post("/incident/close")
async def close():
    if not W.INC:
        raise HTTPException(409, "no incident")
    W.spawn(W.close_incident("closed from the dashboard"))
    return {"ok": True}


@router.post("/incident/stop")
async def stop():
    if W.INC:
        await W.stop_all(W.INC)
        if W.INC.state not in ("CLOSED", "CANCELLED"):
            W.set_state("CLOSED", "stopped from the dashboard")
    return {"ok": True}


# ---------------------------------------------------------------- join links for family / 112 (F8, F1)
def _session(sid: str):
    s = W.INC.sessions.get(sid) if W.INC else None
    if not s:
        raise HTTPException(404, "This Saathi call has ended.")
    return s


@router.get("/api/s/{sid}")
async def session_join_info(sid: str):
    s = _session(sid)
    if s.role != "scene" and W.INC.state not in ("CLOSED", "CANCELLED"):
        await W.ensure_running(s)
    return {"app_id": C.AGORA_APP_ID, "channel": s.channel, "uid": s.user_uid, "token": agora.rtc_token(s.channel, s.user_uid),
            "label": s.label, "role": s.role, "lang": s.lang, "state": W.INC.state}


@router.post("/api/s/{sid}/joined")
async def session_joined(sid: str):
    _session(sid)
    W.spawn(W.on_joined(sid))
    return {"ok": True}
