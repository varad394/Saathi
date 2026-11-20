"""Barebones tools + in-memory session timeline. The real state machine replaces SESSION later."""
import json
import logging
import time

log = logging.getLogger("tools")

# Demo profile. Family numbers live here but are never exposed to the LLM.
PROFILE = {
    "name": "Rahul",
    "blood_group": "B+",
    "allergies": "penicillin",
    "family": [{"relation": "mother", "language": "hi-IN", "phone": "+91XXXXXXXXXX"}],
}

SESSION: dict = {"agent_id": None, "started_at": None, "timeline": []}


def event(kind: str, **data) -> None:
    e = {"t": round(time.time() - (SESSION["started_at"] or time.time()), 2), "kind": kind, **data}
    SESSION["timeline"].append(e)
    log.info("EVENT %s", e)


TOOLS = [
    {"type": "function", "function": {
        "name": "log_rider_status",
        "description": "Record the rider's condition and their exact words. Call whenever the rider says how they are.",
        "parameters": {"type": "object", "properties": {
            "status": {"type": "string", "enum": ["ok", "injured", "no_response", "unclear"]},
            "words": {"type": "string", "description": "What the rider said, verbatim."},
        }, "required": ["status", "words"]},
    }},
    {"type": "function", "function": {
        "name": "get_crash_context",
        "description": "Get the rider's name, crash time and location. Contains no phone numbers.",
        "parameters": {"type": "object", "properties": {}},
    }},
]


def run_tool(name: str, args_json: str) -> str:
    try:
        args = json.loads(args_json or "{}")
    except json.JSONDecodeError:
        args = {}
    if name == "log_rider_status":
        event("rider_status", **args)
        nxt = "cancel" if args.get("status") == "ok" else "escalate"
        return json.dumps({"recorded": True, "next": nxt})
    if name == "get_crash_context":
        event("context_read")
        loc = SESSION.get("location") or {}
        return json.dumps({
            "rider_name": PROFILE["name"],
            "crash_time": time.strftime("%H:%M", time.localtime(SESSION["started_at"] or time.time())),
            "location": "Outer Ring Road near Marathahalli bridge, Bengaluru (demo)",
            "gps": f"{loc['lat']:.5f},{loc['lon']:.5f}" if loc.get("lat") is not None else "unknown",
        })
    return json.dumps({"error": f"unknown tool {name}"})
