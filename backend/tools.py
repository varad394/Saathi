"""Tool schemas (per role and state) and the dispatcher. The state machine decides what is allowed."""
import json
import logging

import protocol as P
import workflow as W

log = logging.getLogger("tools")


def _fn(name, desc, props=None, required=None):
    return {"type": "function", "function": {"name": name, "description": desc, "parameters": {
        "type": "object", "properties": props or {}, "required": required or []}}}


T = {
    "log_rider_status": _fn("log_rider_status", "Record what the RIDER says about himself and his condition.", {
        "status": {"type": "string", "enum": ["ok", "injured", "help", "unclear"],
                   "description": "ok ONLY if the rider himself clearly says he is fine"},
        "words": {"type": "string", "description": "What he said, verbatim"}}, ["status", "words"]),
    "record_facts": _fn("record_facts", "Record EVERY new observation in the latest message about the injured rider, as one list. "
                        "The system then speaks the reviewed first-aid instructions.", {
        "facts": {"type": "array", "items": {"type": "object", "properties": {
            "kind": {"type": "string", "enum": P.FACT_KINDS},
            "detail": {"type": "string", "description": "Short English detail, e.g. 'left leg'"}}, "required": ["kind"]}},
        "speaker": {"type": "string", "enum": ["rider", "bystander", "responder", "unknown"]}}, ["facts", "speaker"]),
    "say_line": _fn("say_line", "Speak a reviewed line for a request: GS1 scared of police/legal trouble; HELMET1 wants to remove helmet; "
                    "WATER1 wants to give water/food/medicine; TRANS1 wants to take him in a vehicle; SAFE1 traffic danger; "
                    "SAFE3 wants to move him; CPR4 helmet during CPR; BREATH2 unsure about breathing; CONS3 ask where it hurts; "
                    "UNC2 recheck breathing; ASK112 bystander should also call 112.", {
        "line_id": {"type": "string", "enum": P.SAYABLE}}, ["line_id"]),
    "ask_ambulance": _fn("ask_ambulance", "A question outside the first-aid protocol: say a holding line and ask the 112 team.", {
        "question": {"type": "string", "description": "The question, in English"}}, ["question"]),
    "answer_question": _fn("answer_question", "The LATEST message answers an open question from family or 112. "
                           "Use ONLY what the person actually said; never guess.", {
        "question_id": {"type": "string"}, "answer": {"type": "string", "description": "The answer, in English"}},
        ["question_id", "answer"]),
    "set_destination": _fn("set_destination", "Someone says which hospital he is being taken to.", {
        "hospital": {"type": "string"}}, ["hospital"]),
    "ambulance_arrived": _fn("ambulance_arrived", "Someone says the ambulance or medical team has arrived."),
    "read_handover": _fn("read_handover", "A paramedic, doctor or nurse asks about the patient (history, blood group, what happened)."),
    "close_incident": _fn("close_incident", "The ambulance has taken him; the job at the scene is done."),
    "ask_scene": _fn("ask_scene", "Ask the people at the crash scene a question you cannot answer from STATUS.", {
        "question": {"type": "string", "description": "The question, in English"}}, ["question"]),
    "reply_to_scene": _fn("reply_to_scene", "Pass the 112 operator's answer or instruction to the bystander.", {
        "message": {"type": "string", "description": "The operator's words, in English"}}, ["message"]),
    "approve_transport": _fn("approve_transport", "The 112 operator says the bystanders should bring the patient themselves."),
    "set_eta": _fn("set_eta", "The 112 operator gives the ambulance arrival time.", {
        "minutes": {"type": "integer"}}, ["minutes"]),
}

SCENE_BY_STATE = {
    "IMPACT": ["log_rider_status"], "DETECTED": ["log_rider_status"],
    "RIDER_CHECK": ["log_rider_status", "record_facts"],
    "CANCEL_PENDING": ["log_rider_status"],
    "BYSTANDER": ["log_rider_status", "record_facts", "say_line", "ask_ambulance", "answer_question", "set_destination", "ambulance_arrived", "read_handover"],
    "COORDINATE": ["log_rider_status", "record_facts", "say_line", "ask_ambulance", "answer_question", "set_destination", "ambulance_arrived", "read_handover"],
    "HANDOVER": ["record_facts", "say_line", "answer_question", "set_destination", "read_handover", "close_incident"],
}
ROLE_TOOLS = {"family": ["ask_scene"], "ambulance": ["ask_scene", "reply_to_scene", "approve_transport", "set_eta", "set_destination"]}


def allowed(s) -> list[dict]:
    names = SCENE_BY_STATE.get(W.INC.state, []) if s.role == "scene" else ROLE_TOOLS.get(s.role, [])
    if s.role != "scene" and W.INC.state in ("CLOSED", "CANCELLED"):
        names = []
    return [T[n] for n in names]


async def run(s, name: str, args_json: str, turn: dict) -> str:
    """Execute a tool. May set turn['say'] (stream verbatim), turn['lines'] (protocol lines) or turn['spoken']."""
    if name not in {t["function"]["name"] for t in allowed(s)}:
        return json.dumps({"error": f"{name} is not allowed in state {W.INC.state}"})
    try:
        a = json.loads(args_json or "{}")
    except json.JSONDecodeError:
        a = {}
    if name == "log_rider_status":
        r = W.rider_status(a.get("status", "unclear"), a.get("words", ""))
        if "_say" in r:
            turn["say"] = r["_say"]
        return json.dumps({"recorded": True})
    if name == "record_facts":
        facts = [f for f in (a.get("facts") or []) if isinstance(f, dict) and f.get("kind") in P.FACT_KINDS]
        ids, critical = W.record_facts(facts, a.get("speaker", "unknown"))
        turn["lines"] += ids
        turn["critical"] |= critical
        return json.dumps({"recorded": [f["kind"] for f in facts], "will_speak": ids})
    if name == "say_line":
        lid = a.get("line_id")
        if lid in P.SAYABLE:
            turn["lines"].append(lid)
        return json.dumps({"will_speak": lid})
    if name == "ask_ambulance":
        turn["lines"].append("HOLD")
        await W.ask_ambulance(a.get("question", ""))
        return json.dumps({"asked_112": True})
    if name == "answer_question":
        return json.dumps(await W.answer_question(a.get("question_id", ""), a.get("answer", "")))
    if name == "set_destination":
        await W.set_destination(a.get("hospital", ""), by=s.role)
        return "Destination recorded and passed on to the family. Acknowledge briefly."
    if name == "ambulance_arrived":
        await W.ambulance_arrived()
        return json.dumps({"state": W.INC.state})
    if name == "read_handover":
        await W.read_handover()
        turn["spoken"] = True
        return json.dumps({"spoken": True})
    if name == "close_incident":
        W.spawn(W.close_incident("closed by the scene agent"))
        return json.dumps({"closing": True})
    if name == "ask_scene":
        await W.ask_scene(s.sid, a.get("question", ""))
        return "Question sent to the people at the scene. Tell the caller, in one short sentence, that you are asking them now."
    if name == "reply_to_scene":
        await W.reply_to_scene(a.get("message", ""))
        return "Passed to the bystander. Acknowledge briefly."
    if name == "approve_transport":
        await W.approve_transport()
        return json.dumps({"approved": True})
    if name == "set_eta":
        await W.set_eta(int(a.get("minutes") or 0))
        return "ETA recorded and passed on. Acknowledge briefly."
    return json.dumps({"error": "unknown tool"})
