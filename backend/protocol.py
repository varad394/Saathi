"""First-aid protocol engine: facts reported by the LLM -> reviewed lines, spoken word for word.

Lines come only from protocol/first_aid.json. The LLM never writes medical text; it only reports facts
(record_fact) or asks for a specific line (say_line).
"""
import json
import pathlib

_DATA = json.loads((pathlib.Path(__file__).parent / "protocol" / "first_aid.json").read_text(encoding="utf-8"))
LINES = {ln["id"]: ln for ln in _DATA["lines"]}
LINE_LANGS = ("en", "hi", "kn")
OFFLINE_LOOP = _DATA["offline_loop"]

# Fact kind -> lines to speak (in order). Facts not listed produce no line.
FACT_LINES = {
    "unresponsive": ["VISOR1", "BREATH1"],
    "not_breathing": ["CPR1", "CPR2", "CPR3"],
    "gasping": ["BREATH2", "CPR1", "CPR2", "CPR3"],
    "breathing_normal": ["UNC1", "BLEED1"],
    "responsive": ["CONS1", "CONS2", "BLEED1"],
    "heavy_bleeding": ["BLEED2", "BLEED3"],
    "bleeding_not_stopping": ["BLEED4"],
    "vomiting": ["VOMIT1", "VOMIT2"],
    "fracture": ["FRAC1"],
    "impaled_object": ["OBJ1"],
    "seizure": ["SEIZ1"],
    "burn": ["BURN1"],
    "multiple_casualties": ["MULTI1"],
    "bike_on_top": ["PIN1"],
    "fire_or_fuel": ["SAFE2"],
    "in_traffic": ["SAFE1"],
    # symptoms the rider reports himself (possible head injury / shock): keep still, help is coming
    "dizzy": ["RIDER_STILL"],
    "headache": ["RIDER_STILL"],
    "nausea": ["RIDER_STILL"],
    "confused": ["RIDER_STILL"],
    "chest_pain": ["RIDER_STILL"],
    "cannot_move_limb": ["RIDER_STILL"],
    "breathing_difficulty": ["RIDER_STILL"],
    "pain_location": ["RIDER_STILL"],
    "symptom": ["RIDER_STILL"],  # ANY other symptom, described by the LLM in `detail`
}
FACT_KINDS = list(FACT_LINES) + ["face_down", "minor_bleeding", "rider_stopped_responding", "other"]

# Order in which lines are spoken when one message reports several things (life threats first).
FACT_PRIORITY = ["not_breathing", "gasping", "heavy_bleeding", "bleeding_not_stopping", "fire_or_fuel", "in_traffic",
                 "vomiting", "unresponsive", "breathing_normal", "seizure", "chest_pain", "breathing_difficulty",
                 "confused", "dizzy", "headache", "nausea", "cannot_move_limb", "responsive", "bike_on_top", "fracture",
                 "impaled_object", "multiple_casualties", "burn"]

# Life threats: spoken with INTERRUPT, not interruptible, and re-briefed to 112 immediately.
CRITICAL_FACTS = {"not_breathing", "gasping", "heavy_bleeding", "bleeding_not_stopping"}
# Facts worth telling the family about.
FAMILY_FACTS = {"unresponsive", "responsive", "not_breathing", "breathing_normal", "heavy_bleeding",
                "rider_stopped_responding", "multiple_casualties", "dizzy", "headache", "confused", "chest_pain",
                "cannot_move_limb", "breathing_difficulty", "pain_location", "symptom"}
# Symptoms the 112 operator should hear about straight away (not life-threat lines, but medically important).
AMBULANCE_FACTS = FAMILY_FACTS

# Lines the LLM may request directly with say_line (requests and reassurance, not assessments).
SAYABLE = ["GS1", "HELMET1", "WATER1", "TRANS1", "SAFE1", "SAFE3", "CPR4", "BREATH2", "CONS3", "UNC2", "ASK112", "HOLD"]


def text(line_id: str, lang: str) -> str:
    ln = LINES[line_id]
    return ln.get(lang if lang in LINE_LANGS else "hi") or ln["en"]


def lines_for_fact(kind: str, facts: list[dict]) -> list[str]:
    ids = list(FACT_LINES.get(kind, []))
    if kind in ("not_breathing", "gasping") and any(f["kind"] == "face_down" for f in facts):
        ids.insert(0, "CPR0")
    return ids


def line_lang(scene_lang: str) -> str:
    """Language for protocol lines: the bystander's language if we have reviewed lines in it, else Hindi."""
    return scene_lang if scene_lang in LINE_LANGS else "hi"
