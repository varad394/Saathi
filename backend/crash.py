"""Crash lifecycle events from the phone. Detection runs entirely on the phone;
no sensor data comes here, only these three events.

  impact     -> POST /crash/impact     -> pre-warm the ConvoAI agent (hides ~2 s agent start)
  confirmed  -> POST /crash/confirmed  -> phone joins the channel, agent greets
  cancelled  -> POST /crash/cancel     -> stop the pre-warmed agent
"""
import logging

from fastapi import APIRouter
from pydantic import BaseModel

import agora
import tools

log = logging.getLogger("crash")
router = APIRouter(prefix="/crash")


class ImpactIn(BaseModel):
    peak_g: float
    lat: float | None = None
    lon: float | None = None
    speed_kmh: float | None = None


@router.post("/impact")
async def impact(body: ImpactIn):
    from main import start_agent  # late import: main imports this module

    tools.SESSION["location"] = {"lat": body.lat, "lon": body.lon}
    return await start_agent(reason="impact", peak_g=body.peak_g, speed_kmh=body.speed_kmh)


class ConfirmIn(BaseModel):
    peak_g: float
    angle_deg: float
    still_std_g: float


@router.post("/confirmed")
def confirmed(body: ConfirmIn):
    tools.event("crash_confirmed", **body.model_dump())
    return {"ok": True}


class CancelIn(BaseModel):
    reason: str


@router.post("/cancel")
async def cancel(body: CancelIn):
    tools.event("detector_cancelled", reason=body.reason)
    aid = tools.SESSION.get("agent_id")
    if aid:
        try:
            await agora.leave(aid)
        except Exception:
            log.exception("leave failed")
        tools.SESSION["agent_id"] = None
    return {"ok": True}
