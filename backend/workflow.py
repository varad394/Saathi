"""Incident state machine and orchestration. The backend decides; the LLM only understands and picks tools.

States: IMPACT -> DETECTED -> RIDER_CHECK -> (CANCEL_PENDING -> CANCELLED)
                                          -> BYSTANDER -> COORDINATE -> HANDOVER -> CLOSED
Scenario IDs (C4, F8, G1, ...) refer to docs/scenario_tree.md.
"""
import asyncio
import json
import logging
import pathlib
import re
import time
import uuid
from dataclasses import dataclass, field

import agora
import compose
import config as C
import lang as L
import protocol as P
import settings as S

log = logging.getLogger("workflow")
_DATA = pathlib.Path(__file__).parent / "data"
PROFILE = json.loads((_DATA / "profile.json").read_text(encoding="utf-8"))
if (_DATA / "profile.local.json").exists():  # real demo numbers, git-ignored
    PROFILE |= {k: v for k, v in json.loads((_DATA / "profile.local.json").read_text(encoding="utf-8")).items() if not k.startswith("_")}
RIDER = PROFILE["rider"]

# Timers: live values come from settings.py (changeable from the dashboard / phone). Fixed ones:
ANNOUNCE_MAX = 8
RECHECK_EVERY_S = 120
STOP_DELAY_S = 25
REPEAT_GUARD_S = 45

SCENE_SPEECH_LANGS = {"en", "hi", "kn", "ta", "te"}  # what the scene voice (en-IN-pooja) speaks

# Fixed rider-facing lines (not medical), spoken verbatim
RIDER_LINES = {
    "cancel_ack": {"en": "Okay, I am cancelling the alert. Say help if you need me.",
                   "hi": "ठीक है, मैं अलर्ट रद्द कर रही हूँ। मदद चाहिए तो हेल्प बोलिए।"},
    "escalate_ack": {"en": "I am calling your family and an ambulance now. Please stay still. Where does it hurt?",
                     "hi": "मैं अभी आपके परिवार और एम्बुलेंस को बुला रही हूँ। कृपया हिलिए मत। दर्द कहाँ हो रहा है?"},
    "still_here": {"en": "Okay. Help is still on the way; the ambulance team will check you.",
                   "hi": "ठीक है। मदद आ रही है, एम्बुलेंस टीम आपको देखेगी।"},
    # a bystander cannot cancel for the rider (C7); a bystander reporting injury escalates
    "bystander_no_cancel": {"en": "Thank you. Unless he tells me himself that he is fine, I will still call for help.",
                            "hi": "धन्यवाद। जब तक वो खुद नहीं कहते कि वो ठीक हैं, मैं मदद बुलाऊँगी।",
                            "kn": "ಧನ್ಯವಾದ. ಅವರೇ ತಾವು ಚೆನ್ನಾಗಿದ್ದೇನೆ ಎಂದು ಹೇಳದಿದ್ದರೆ, ನಾನು ಸಹಾಯಕ್ಕೆ ಕರೆ ಮಾಡುತ್ತೇನೆ."},
    "bystander_escalate": {"en": "Thank you. I am calling his family and an ambulance now. Please stay with him.",
                           "hi": "धन्यवाद। मैं अभी इनके परिवार और एम्बुलेंस को बुला रही हूँ। कृपया इनके पास रहिए।",
                           "kn": "ಧನ್ಯವಾದ. ನಾನು ಈಗಲೇ ಅವರ ಕುಟುಂಬ ಮತ್ತು ಆಂಬ್ಯುಲೆನ್ಸ್‌ಗೆ ಕರೆ ಮಾಡುತ್ತಿದ್ದೇನೆ. ದಯವಿಟ್ಟು ಅವರ ಜೊತೆ ಇರಿ."},
}
GREETING_SCENE = ("साथी बोल रही हूँ। आप ठीक हैं? ठीक नहीं बोला, तो मैं मदद बुला लूँगी। "
                  "Saathi here. Are you okay? Say I'm fine, or I'll call your family and an ambulance.")


@dataclass
class Session:
    sid: str
    role: str  # scene | family | ambulance
    label: str
    lang: str
    voice: str
    locale: str
    asr_lang: str
    channel: str
    agent_uid: int = 999
    user_uid: int = 1001
    contact_id: str | None = None
    system_prompt: str = ""
    greeting: str = ""
    agent_id: str | None = None
    status: str = "new"  # new | starting | running | joined | stopped | failed
    joined_at: float | None = None

    def public(self) -> dict:
        return {k: getattr(self, k) for k in ("sid", "role", "label", "lang", "voice", "status", "agent_id")} | {
            "link": f"/j/{self.sid}" if self.role != "scene" else None,
            "url": f"{C.PUBLIC_BASE_URL}/j/{self.sid}" if self.role != "scene" else None}


@dataclass
class Incident:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:6])
    created: float = field(default_factory=time.time)
    state: str = "IMPACT"
    peak_g: float = 0.0
    location: dict = field(default_factory=dict)
    scene_lang: str = "hi"
    rider_lang: str = "hi"
    rider: dict = field(default_factory=lambda: {"status": None, "words": [], "last_answer_at": None})
    facts: list = field(default_factory=list)
    actions: dict = field(default_factory=dict)  # name -> {"status", "t", "detail"}
    questions: list = field(default_factory=list)
    destination: str | None = None
    eta_min: int | None = None
    flags: set = field(default_factory=set)
    sessions: dict = field(default_factory=dict)
    timeline: list = field(default_factory=list)
    spoken: dict = field(default_factory=dict)  # line id -> last spoken time
    last_heard: float = 0.0
    lang_candidate: str | None = None
    summary: str | None = None
    tasks: list = field(default_factory=list)
    rider_check_deadline: float | None = None
    asr_vendor: str = C.ASR_VENDOR

    def t(self) -> float:
        return round(time.time() - self.created, 1)

    def clock(self, ts: float | None = None) -> str:
        return time.strftime("%H:%M:%S", time.localtime(ts or time.time()))

    def scene(self) -> Session:
        return next(s for s in self.sessions.values() if s.role == "scene")

    def by_role(self, role: str) -> list[Session]:
        return [s for s in self.sessions.values() if s.role == role]

    def public(self) -> dict:
        return {
            "id": self.id, "state": self.state, "t": self.t(), "created": self.clock(self.created),
            "rider_check_left": max(0, round(self.rider_check_deadline - time.time(), 1)) if self.rider_check_deadline and self.state == "RIDER_CHECK" else None,
            "peak_g": round(self.peak_g, 2), "location": self.location, "scene_lang": self.scene_lang,
            "rider": self.rider, "facts": self.facts, "actions": self.actions, "questions": self.questions,
            "destination": self.destination, "eta_min": self.eta_min, "flags": sorted(self.flags),
            "sessions": [s.public() for s in self.sessions.values()], "timeline": self.timeline[-80:],
            "transcript": [{"who": "them" if e["kind"] == "heard" else "saathi", "text": e["text"], "clock": e["clock"]}
                           for e in self.timeline if e["kind"] in ("heard", "spoke", "said")
                           and e.get("sid", "").endswith("-scene") and e.get("text", "").strip()][-14:],
            "summary": self.summary,
        }


INC: Incident | None = None


# ---------------------------------------------------------------- helpers
def ev(kind: str, **data) -> None:
    if INC is None:
        return
    e = {"t": INC.t(), "clock": INC.clock(), "kind": kind, **data}
    INC.timeline.append(e)
    log.info("EVENT %s", json.dumps(e, ensure_ascii=False)[:400])


def set_state(new: str, why: str = "") -> None:
    old = INC.state
    INC.state = new
    ev("state", frm=old, to=new, why=why)


def action(name: str, status: str, detail: str = "") -> None:
    INC.actions[name] = {"status": status, "t": INC.clock(), "detail": detail}
    ev("action", name=name, status=status, detail=detail)


def spawn(coro) -> None:
    async def guard():
        try:
            await coro
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception("background task failed")
    INC.tasks.append(asyncio.create_task(guard()))


def llm_url(sid: str) -> str:
    return f"{C.PUBLIC_BASE_URL}/llm/{sid}/chat/completions"


async def start_session(s: Session) -> bool:
    s.status = "starting"
    try:
        res = await agora.join(name=f"saathi-{INC.id}-{s.role}-{s.contact_id or 'x'}-{int(time.time())}",
                               channel=s.channel, agent_uid=s.agent_uid, user_uid=s.user_uid, llm_url=llm_url(s.sid),
                               system_prompt=s.system_prompt, greeting=s.greeting, voice=s.voice, locale=s.locale,
                               asr_lang=s.asr_lang, idle_timeout=180, asr_vendor=INC.asr_vendor)
        s.agent_id, s.status = res.get("agent_id"), "running"
        ev("session_started", sid=s.sid, role=s.role, agent_id=s.agent_id)
        return True
    except Exception as e:
        s.status = "failed"
        ev("session_failed", sid=s.sid, role=s.role, error=str(e)[:200])
        return False


async def ensure_running(s: Session) -> None:
    """Re-start an agent that has exited (e.g. idle timeout before the family opened the link)."""
    if s.agent_id:
        q = await agora.query(s.agent_id)
        if q.get("status") in ("RUNNING", "STARTING", "IDLE"):
            return
    await start_session(s)


async def say(s: Session | None, text: str, priority: str = "APPEND", interruptable: bool = True) -> None:
    if not s or not s.agent_id or s.status not in ("running", "joined") or not text:
        return
    try:
        await agora.speak(s.agent_id, text, priority, interruptable)
        ev("spoke", sid=s.sid, text=text)
    except Exception as e:
        ev("speak_failed", sid=s.sid, error=str(e)[:200])


async def say_lines(ids: list[str], critical: bool = False, force: set | None = None) -> list[str]:
    """Speak reviewed protocol lines word for word in the bystander's language. Automatic lines are not repeated
    within REPEAT_GUARD_S; lines someone explicitly asked for (`force`) always play."""
    now = time.time()
    force = force or set()
    ids = [i for i in ids if critical or i in force or now - INC.spoken.get(i, 0) > REPEAT_GUARD_S]
    if not ids:
        return []
    lg = P.line_lang(INC.scene_lang)
    chunks, cur = [], ""
    for i in ids:
        INC.spoken[i] = now
        t = P.text(i, lg)
        cand = (cur + " " + t).strip()
        if len(cand.encode("utf-8")) > agora.SPEAK_LIMIT - 12:
            chunks.append(cur)
            cand = t
        cur = cand
    chunks.append(cur)
    ev("protocol", lines=ids, lang=lg, critical=critical)
    for n, c in enumerate(chunks):
        await say(INC.scene(), c, priority="INTERRUPT" if (critical and n == 0) else "APPEND", interruptable=not critical)
    return ids


async def say_composed(s: Session | None, text_en: str, audience: str = "") -> None:
    if not s or s.status not in ("running", "joined"):
        return
    await say(s, await compose.to_lang(text_en, s.lang if s.role != "scene" else INC.scene_lang, audience))


def facts_of(kind: str) -> list[dict]:
    return [f for f in INC.facts if f["kind"] == kind]


# ---------------------------------------------------------------- briefings (deterministic templates)
def condition_en() -> str:
    parts = []
    if INC.rider["words"]:
        first = INC.rider["words"][0]
        parts.append(f'At first he was talking and said: "{first["text"]}".')
    if facts_of("rider_stopped_responding") or facts_of("unresponsive"):
        parts.append("Now he is not answering.")
    if facts_of("responsive"):
        parts.append("He is awake and responding.")
    if facts_of("not_breathing") or facts_of("gasping"):
        parts.append("He is not breathing normally; a person there is doing chest compressions.")
    elif facts_of("breathing_normal"):
        parts.append("He is breathing.")
    if facts_of("heavy_bleeding"):
        parts.append("He is bleeding heavily, and someone is pressing on the wound.")
    symptoms = [k.replace("_", " ") for k in ("dizzy", "headache", "nausea", "confused", "chest_pain",
                                               "cannot_move_limb", "breathing_difficulty") if facts_of(k)]
    if symptoms:
        parts.append(f"He reported: {', '.join(symptoms)}.")
    other = [f["detail"] for f in facts_of("symptom") if f.get("detail")]
    if other:
        parts.append(f"He also said: {'; '.join(other)}.")
    pain = facts_of("pain_location")
    if pain:
        parts.append(f"He has pain in: {', '.join(f['detail'] or 'unspecified' for f in pain)}.")
    if INC.rider["status"] == "ok" and INC.state not in ("CANCEL_PENDING", "CANCELLED"):
        parts.append("He has said he is okay, but the ambulance team will check him.")
    return " ".join(parts) or "I don't know his condition yet."


def family_brief_en(contact: dict) -> str:
    loc = INC.location.get("text") or "an unknown place"
    amb = ("The ambulance service has been informed." if INC.actions.get("ambulance", {}).get("status") == "briefed"
           else "I am informing the ambulance service now.")
    help_ = "A person at the scene is helping him." if "engaged" in INC.flags else "I am asking people nearby to help him."
    dest = f" They are taking him to {INC.destination}." if INC.destination else ""
    return (f"{RIDER['name']} has had a road accident at {INC.clock(INC.created)[:5]} on {loc}. {condition_en()} "
            f"{amb} {help_}{dest} I will keep you updated. You can ask me questions.")


def ambulance_brief_en() -> str:
    loc = INC.location
    gps = f" GPS {loc['lat']:.5f}, {loc['lon']:.5f}." if loc.get("lat") is not None else ""
    return (f"Two-wheeler road crash at {INC.clock(INC.created)[:5]}. Location: {loc.get('text', 'unknown')}.{gps} "
            f"Patient: {RIDER['sex']}, about {RIDER['age']} years, blood group {RIDER['blood_group']}, allergic to {RIDER['allergies']}. "
            f"{condition_en()} Bystander present: {'yes' if 'engaged' in INC.flags else 'not yet'}. "
            "Saathi is guiding the bystander with standard first aid. You can ask me questions, or give instructions for the bystander.")


def handover_en() -> str:
    """G1: read from a template, so the medical profile never enters the LLM."""
    r = RIDER
    said = "; ".join(f'at {w["clock"][:5]} he said "{w["text"]}"' for w in INC.rider["words"][:3])
    facts = "; ".join(f'{f["kind"].replace("_", " ")}{(" (" + f["detail"] + ")") if f.get("detail") else ""} at {f["clock"][:5]}'
                      for f in INC.facts if f["kind"] != "other")
    aid = ", ".join(sorted({i for i in INC.spoken if i[:3] in ("CPR", "BLE", "UNC", "VOM", "CON")})) or "none"
    told = ", ".join(n for n, a in INC.actions.items() if a["status"] in ("briefed", "reached", "link_ready")) or "none"
    return (f"Handover from Saathi. Patient {r['name']}, {r['sex']}, {r['age']}. Blood group {r['blood_group']}. "
            f"Allergies: {r['allergies']}. Conditions: {r['conditions']}. Medicines: {r['medicines']}. "
            f"Crash at {INC.clock(INC.created)[:5]}, impact about {INC.peak_g:.1f} g. "
            f"{('Rider: ' + said + '.') if said else 'The rider did not speak.'} "
            f"{('Observed: ' + facts + '.') if facts else ''} First-aid instructions given: {aid}. Informed: {told}.")


# ---------------------------------------------------------------- lifecycle
async def stop_all(inc: Incident) -> None:
    cur = asyncio.current_task()
    for t in inc.tasks:
        if t is not cur:  # never cancel the task that is doing the stopping
            t.cancel()
    for s in inc.sessions.values():
        if s.agent_id and s.status not in ("stopped", "failed"):
            try:
                await agora.leave(s.agent_id)
            except Exception:
                log.exception("leave failed for %s", s.sid)
            s.status = "stopped"


async def on_impact(peak_g: float, lat: float | None = None, lon: float | None = None, speed_kmh: float | None = None,
                    asr_vendor: str | None = None) -> dict:
    """Phone sensed an impact: create the incident and pre-warm the scene agent (hides ~2 s start time)."""
    global INC
    if INC:
        await stop_all(INC)  # also cancels its timers, so they can never touch the new incident
    INC = Incident(peak_g=peak_g, asr_vendor=asr_vendor or S.get('asr_vendor'))
    INC.location = {"text": PROFILE["demo_location"]["text"],
                    "lat": lat if lat is not None else PROFILE["demo_location"]["lat"],
                    "lon": lon if lon is not None else PROFILE["demo_location"]["lon"]}
    INC.rider_lang = RIDER["rider_check_languages"][0]
    INC.scene_lang = INC.rider_lang
    ev("impact", peak_g=round(peak_g, 2), speed_kmh=speed_kmh, asr=INC.asr_vendor)
    scene = Session(sid=f"{INC.id}-scene", role="scene", label="Rider and bystanders", lang=INC.scene_lang,
                    voice=C.MURF_VOICE_ID, locale="en-IN", asr_lang="unknown", channel=f"saathi-{INC.id}",
                    system_prompt=SCENE_PROMPT, greeting=GREETING_SCENE)
    INC.sessions[scene.sid] = scene
    await start_session(scene)
    return {"incident": INC.id, "sid": scene.sid, "agent_id": scene.agent_id, "status": scene.status, "app_id": C.AGORA_APP_ID,
            "channel": scene.channel, "uid": scene.user_uid, "token": agora.rtc_token(scene.channel, scene.user_uid)}


async def on_confirmed(peak_g: float, angle_deg: float, still_std_g: float) -> None:
    if INC is None or INC.state != "IMPACT":
        return
    INC.peak_g = max(INC.peak_g, peak_g)
    set_state("DETECTED", f"still and tilted {angle_deg:.0f} deg")
    set_state("RIDER_CHECK", f"{S.get('rider_check_s')} s to answer after the greeting")
    spawn(_rider_check_timer())


async def on_detector_cancel(reason: str) -> None:
    """False alarm on the phone before confirmation (kept moving / no tilt)."""
    if INC and INC.state == "IMPACT":
        set_state("CANCELLED", f"detector: {reason}")
        await stop_all(INC)


async def _rider_check_timer() -> None:
    """The rider gets S.get('rider_check_s') seconds AFTER the greeting. The greeting plays when the phone joins the channel,
    so wait for the join report (dashboard / app call /api/s/{sid}/joined); fall back after 15 s if none arrives."""
    inc = INC
    waited = 0.0
    while inc.scene().status != "joined" and waited < 15 and INC is inc:
        await asyncio.sleep(0.25)
        waited += 0.25
    inc.rider_check_deadline = time.time() + S.get('greeting_s') + S.get('rider_check_s')
    ev("rider_check_window", seconds=S.get('greeting_s') + S.get('rider_check_s'), phone_joined=inc.scene().status == "joined")
    await asyncio.sleep(S.get('greeting_s') + S.get('rider_check_s'))
    if INC is inc and inc.state == "RIDER_CHECK":
        await escalate("no answer from the rider in 20 s", rider_talking=False)


async def _cancel_finalize() -> None:
    inc = INC
    await asyncio.sleep(S.get('cancel_undo_s'))
    if INC is not inc or inc.state != "CANCEL_PENDING":
        return
    set_state("CANCELLED", "rider said he is fine")
    if INC.by_role("family"):  # F17 false-alarm callback
        for s in INC.by_role("family"):
            await say_composed(s, f"False alarm. {RIDER['name']} answered himself and says he is okay. Sorry for the worry.")
        action("false_alarm_callback", "sent")
    await asyncio.sleep(S.get('listen_after_cancel_s'))
    if INC is inc and inc.state == "CANCELLED":  # nobody asked for help: end the call
        ev("listening_ended", after_s=S.get('listen_after_cancel_s'))
        await stop_all(inc)


async def escalate(reason: str, rider_talking: bool) -> None:
    if INC.state in ("BYSTANDER", "COORDINATE", "HANDOVER", "CLOSED"):
        return
    INC.rider_check_deadline = None
    set_state("BYSTANDER", reason)
    if rider_talking:
        INC.flags.add("rider_talking")
    spawn(_start_family())
    spawn(_start_ambulance())
    spawn(_bystander_watch(rider_talking))


async def _bystander_watch(rider_talking: bool) -> None:
    if rider_talking:  # C4: rider answered, then went silent
        INC.last_heard = time.time()
        while INC.state == "BYSTANDER" and time.time() - INC.last_heard < S.get('rider_silent_s'):
            await asyncio.sleep(1)
        if INC.state != "BYSTANDER":
            return
        record_fact("rider_stopped_responding", f"no answer for {S.get('rider_silent_s')} s", "system")
    n = 0
    while INC.state == "BYSTANDER" and "engaged" not in INC.flags and n < ANNOUNCE_MAX:
        INC.flags.add("announced")
        for lg in dict.fromkeys([RIDER["local_language"], "hi", "en"]):
            await say(INC.scene(), P.text("AN1", lg if lg in P.LINE_LANGS else "en"))
        ev("announced", n=n + 1)
        n += 1
        await asyncio.sleep(S.get('announce_every_s'))


async def _recheck_loop() -> None:  # E5: unconscious but breathing -> ask every 2 min
    while INC.state in ("BYSTANDER", "COORDINATE"):
        await asyncio.sleep(RECHECK_EVERY_S)
        if INC.state in ("BYSTANDER", "COORDINATE"):
            await say_lines(["UNC2"])


# ---------------------------------------------------------------- outbound sessions (F1, F8)
async def _start_family() -> None:
    for c in sorted(PROFILE["contacts"], key=lambda c: c["priority"]):
        voice, locale = C.VOICE_BY_LANG.get(c["language"], (C.MURF_VOICE_ID, "en-IN"))
        greeting = await compose.to_lang(f"Hello, this is Saathi, calling from {RIDER['name']}'s phone about {RIDER['name']}. Please listen.", c["language"])
        s = Session(sid=f"{INC.id}-fam-{c['id']}", role="family", label=f"{c['relation'].title()} ({L.NAMES.get(c['language'])})",
                    lang=c["language"], voice=voice, locale=locale, asr_lang=locale, channel=f"saathi-{INC.id}-{c['id']}",
                    user_uid=2001, contact_id=c["id"], greeting=greeting,
                    system_prompt=FAMILY_PROMPT.format(relation=c["relation"], rider=RIDER["name"], lang=L.NAMES.get(c["language"])))
        INC.sessions[s.sid] = s
        ok = await start_session(s)
        # The phone (or SMS fallback) delivers the link; the number itself never reaches the LLM.
        action(f"family:{c['id']}", "link_ready" if ok else "failed", f"{s.label}: /j/{s.sid}")


async def _start_ambulance() -> None:
    s = Session(sid=f"{INC.id}-amb", role="ambulance", label="112 operator (demo)", lang="en", voice=C.MURF_VOICE_ID,
                locale="en-IN", asr_lang="en-IN", channel=f"saathi-{INC.id}-112", user_uid=3001,
                greeting="This is Saathi, an automated emergency app, reporting a road crash. Please listen.",
                system_prompt=AMBULANCE_PROMPT)
    INC.sessions[s.sid] = s
    ok = await start_session(s)
    action("ambulance", "calling" if ok else "failed", f"/j/{s.sid}")
    if not ok:
        await say_lines(["ASK112"])


async def on_joined(sid: str) -> None:
    """A family member / 112 operator opened their link. Brief them, then confirm at the scene (Q44 confirm)."""
    s = INC.sessions.get(sid) if INC else None
    if not s or s.status == "joined":
        return
    s.status, s.joined_at = "joined", time.time()
    ev("joined", sid=sid, role=s.role)
    if s.role == "scene":
        return
    if s.role == "family":
        contact = next(c for c in PROFILE["contacts"] if c["id"] == s.contact_id)
        await say_composed(s, family_brief_en(contact), audience=f"the rider's {contact['relation']}")
        action(f"family:{s.contact_id}", "reached", s.label)
        await say_composed(INC.scene(), f"I have reached his {contact['relation']}. She knows what happened.")
    elif s.role == "ambulance":
        await say(s, ambulance_brief_en())
        action("ambulance", "briefed", "location and condition shared")
        await say_composed(INC.scene(), "The ambulance team has his location and condition.")


# ---------------------------------------------------------------- scene events (called from tools / llm)
def on_utterance(s: Session, text: str) -> bool:
    """Every user turn. Returns True if this turn is the first bystander reply (engagement)."""
    INC.last_heard = time.time()
    ev("heard", sid=s.sid, text=text)
    if s.role == "ambulance" and INC.eta_min is None:
        m = re.search(r"(\d{1,2})\s*(?:min|minute)", text.lower())
        if m:
            spawn(set_eta(int(m.group(1))))
    if s.role != "scene":
        return False
    code = L.detect(text)
    if code:  # sticky switching (section 9.3)
        target = code if code in SCENE_SPEECH_LANGS else "hi"
        if target != INC.scene_lang and (L.word_count(text) >= 3 or INC.lang_candidate == target):
            ev("language", frm=INC.scene_lang, to=target, detected=code)
            INC.scene_lang = target
        INC.lang_candidate = target
        if INC.state in ("IMPACT", "DETECTED", "RIDER_CHECK", "CANCEL_PENDING") and target in ("hi", "en"):
            INC.rider_lang = target
    if INC.state == "BYSTANDER" and "announced" in INC.flags and "engaged" not in INC.flags:
        INC.flags.add("engaged")
        set_state("COORDINATE", "a bystander answered")
        return True
    return False


def rider_status(status: str, words: str, speaker: str = "rider") -> dict:
    if speaker == "bystander":  # C7: only the rider can cancel; a bystander's report is a fact, not consent
        d = L.detect(words)
        lg = d if d in ("en", "hi", "kn") else (INC.scene_lang if INC.scene_lang in ("en", "hi", "kn") else "en")
        ev("bystander_says", status=status, words=words)
        if status == "ok":
            INC.facts.append({"kind": "responsive" if "fine" in words.lower() else "other", "detail": f"bystander: {words}",
                              "speaker": "bystander", "clock": INC.clock(), "ts": time.time()})
            return {"_say": RIDER_LINES["bystander_no_cancel"][lg]} if INC.state in ("RIDER_CHECK", "CANCEL_PENDING") else {"recorded": True}
        if INC.state in ("IMPACT", "DETECTED", "RIDER_CHECK", "CANCEL_PENDING", "CANCELLED"):
            spawn(escalate(f"bystander: {words or status}", rider_talking=False))
            return {"_say": RIDER_LINES["bystander_escalate"][lg]}
        return {"recorded": True}
    INC.rider["status"] = status
    INC.rider["last_answer_at"] = INC.clock()
    if words:
        INC.rider["words"].append({"text": words, "clock": INC.clock(), "status": status})
    ev("rider_status", status=status, words=words)
    lg = INC.rider_lang if INC.rider_lang in ("hi", "en") else "hi"
    if INC.state in ("IMPACT", "DETECTED", "RIDER_CHECK"):
        if status == "ok":
            set_state("CANCEL_PENDING", f"rider: {words}")
            INC.rider_check_deadline = None
            spawn(_cancel_finalize())
            return {"_say": RIDER_LINES["cancel_ack"][lg]}
        spawn(escalate(f"rider: {words or status}", rider_talking=True))
        return {"_say": RIDER_LINES["escalate_ack"][lg]}
    if INC.state in ("CANCEL_PENDING", "CANCELLED") and status != "ok":
        spawn(escalate(f"rider changed his mind: {words}", rider_talking=True))
        return {"_say": RIDER_LINES["escalate_ack"][lg]}
    if status == "ok" and INC.state in ("BYSTANDER", "COORDINATE"):  # C10: recorded, not acted on
        spawn(_relay_family(f"{RIDER['name']} has said he is okay. The ambulance team will still check him."))
        return {"_say": RIDER_LINES["still_here"][lg]}
    return {"recorded": True}


def record_facts(facts: list[dict], speaker: str) -> tuple[list[str], bool]:
    """Several observations from one message -> one ordered list of protocol lines (life threats first)."""
    order = {k: i for i, k in enumerate(P.FACT_PRIORITY)}
    facts = sorted(facts, key=lambda f: order.get(f["kind"], 99))
    now = time.time()
    ids, kinds = [], set()
    for f in facts:
        k = f["kind"]
        recent = [x for x in INC.facts if x["kind"] == k and now - x.get("ts", 0) < 90]
        if recent and k not in P.CRITICAL_FACTS:
            continue  # already known; don't repeat instructions
        kinds.add(k)
        ids += record_fact(k, f.get("detail", ""), speaker)
    if kinds - {"other"} and INC.state in ("IMPACT", "DETECTED", "RIDER_CHECK", "CANCEL_PENDING", "CANCELLED"):
        # any real injury or symptom reported before escalation means help is needed now
        spawn(escalate(f"{speaker} reported: {', '.join(sorted(kinds))}", rider_talking=speaker == "rider"))
    known = {x["kind"] for x in INC.facts}
    if known & {"heavy_bleeding", "minor_bleeding", "bleeding_not_stopping"}:
        ids = [i for i in ids if i != "BLEED1"]  # don't ask about bleeding we already know about
    if kinds & {"not_breathing", "gasping"}:
        ids = [i for i in ids if i not in ("VISOR1", "BREATH1", "UNC1")]
    return list(dict.fromkeys(ids)), bool(kinds & P.CRITICAL_FACTS)


def record_fact(kind: str, detail: str = "", speaker: str = "unknown") -> list[str]:
    f = {"kind": kind, "detail": detail, "speaker": speaker, "clock": INC.clock(), "ts": time.time()}
    INC.facts.append(f)
    ev("fact", fact=kind, detail=detail, speaker=speaker)
    if kind == "breathing_normal" and (facts_of("unresponsive") or facts_of("rider_stopped_responding")) and "recheck" not in INC.flags:
        INC.flags.add("recheck")
        spawn(_recheck_loop())
    if kind in P.CRITICAL_FACTS:
        amb = INC.by_role("ambulance")
        if amb:
            spawn(say(amb[0], f"Priority update: {kind.replace('_', ' ')}{(', ' + detail) if detail else ''}.", priority="INTERRUPT"))
    if kind in P.FAMILY_FACTS:
        spawn(_relay_family(condition_en()))
    if kind in P.AMBULANCE_FACTS and kind not in P.CRITICAL_FACTS:
        for a in INC.by_role("ambulance"):
            if a.status == "joined":
                spawn(say(a, f"Update: {kind.replace('_', ' ')}{(', ' + detail) if detail else ''}."))
    return P.lines_for_fact(kind, INC.facts)


async def _relay_family(text_en: str) -> None:
    for s in INC.by_role("family"):
        if s.status == "joined":
            await say_composed(s, text_en, audience="the rider's family")


async def ask_scene(from_sid: str, question_en: str) -> dict:
    q = {"id": f"q{len(INC.questions) + 1}", "from": from_sid, "from_label": INC.sessions[from_sid].label,
         "question": question_en, "asked": INC.clock(), "answer": None}
    INC.questions.append(q)
    ev("question", **q)
    who = INC.sessions[from_sid]
    asker = "The ambulance team" if who.role == "ambulance" else f"His {next(c['relation'] for c in PROFILE['contacts'] if c['id'] == who.contact_id)}"
    await say_composed(INC.scene(), f'{asker} is asking you this question: "{question_en}"',
                       audience="a bystander at a crash scene. This is a QUESTION for them: keep it a question addressed to them")
    return {"asked": True, "id": q["id"]}


async def answer_question(qid: str, answer_en: str) -> dict:
    q = next((q for q in INC.questions if q["id"] == qid), None)
    if not q:
        return {"error": "no such question"}
    q["answer"], q["answered"] = answer_en, INC.clock()
    ev("answer", id=qid, answer=answer_en)
    asker = INC.sessions.get(q["from"])
    if asker and asker.role == "ambulance":
        await say(asker, f"Answer from the scene to '{q['question']}': {answer_en}")
    else:
        await say_composed(asker, f'You asked: "{q["question"]}". The people with {RIDER["name"]} answered: "{answer_en}".',
                           audience="the rider's family")
    if "hospital" in q["question"].lower() and not INC.destination:  # deterministic backup for set_destination
        await set_destination(answer_en, by="scene", tell_family=False)  # family just heard the answer
    return {"answered": True}


async def ask_ambulance(question_en: str) -> None:
    amb = INC.by_role("ambulance")
    ev("question_to_112", question=question_en)
    if amb:
        await say(amb[0], f"Question from the bystander: {question_en}")


async def reply_to_scene(message_en: str) -> None:
    ev("from_112", message=message_en)
    await say_composed(INC.scene(), f"The ambulance team says: {message_en}", audience="a bystander at a crash scene")


async def approve_transport() -> None:
    INC.flags.add("transport_approved")
    ev("transport_approved")
    await say_lines(["TRANS2"])
    await _relay_family("The ambulance team has asked the people there to bring him to hospital.")


async def set_destination(name: str, by: str, tell_family: bool = True) -> None:
    if INC.destination and (name.lower() in INC.destination.lower() or INC.destination.lower() in name.lower()):
        return  # already known: relay once
    INC.destination = name
    ev("destination", name=name, by=by)
    if tell_family:
        await _relay_family(f"They are taking {RIDER['name']} to {name}.")
    if by != "ambulance":
        for a in INC.by_role("ambulance"):
            await say(a, f"Update: bystander says he is being taken to {name}.")


async def set_eta(minutes: int) -> None:
    if not minutes or INC.eta_min == minutes:
        return  # relay once
    INC.eta_min = minutes
    ev("eta", minutes=minutes)
    await say_composed(INC.scene(), f"The ambulance should arrive in about {minutes} minutes.")
    await _relay_family(f"The ambulance should reach him in about {minutes} minutes.")


async def ambulance_arrived() -> None:
    if INC.state in ("HANDOVER", "CLOSED"):
        return
    set_state("HANDOVER", "ambulance at the scene")
    await _relay_family(f"The ambulance has reached {RIDER['name']}. The medical team is with him now.")


async def read_handover() -> None:
    if INC.state not in ("HANDOVER", "CLOSED"):
        set_state("HANDOVER", "responder asked about the patient")
    text = handover_en()
    ev("handover", text=text)
    await say(INC.scene(), text, priority="INTERRUPT", interruptable=False)


async def close_incident(reason: str = "handover complete") -> None:
    if INC is None or INC.state in ("CLOSED", "CANCELLED"):
        return
    inc = INC
    set_state("CLOSED", reason)
    INC.summary = (f"Saathi summary: {RIDER['name']} had a road accident at {INC.clock(INC.created)[:5]} on {INC.location.get('text')}. "
                   f"{condition_en()} " + (f"He was taken to {INC.destination}. " if INC.destination else "")
                   + "The ambulance team took over.")
    ev("summary", text=INC.summary)
    action("summary", "sent", "family (voice now; SMS from the phone)")
    await _relay_family(INC.summary)
    await asyncio.sleep(STOP_DELAY_S)
    await stop_all(inc)


# ---------------------------------------------------------------- per-turn status for each role's LLM
def status_for(s: Session) -> str:
    done = [f"{n}: {a['status']} at {a['t']}" for n, a in INC.actions.items()]
    facts = [f"{f['kind']}{(' (' + f['detail'] + ')') if f['detail'] else ''} - {f['speaker']} at {f['clock']}" for f in INC.facts]
    words = [f'"{w["text"]}" at {w["clock"]}' for w in INC.rider["words"]]
    lines = [f"STATE: {INC.state}. Time since crash: {int(INC.t())} s. Rider: {RIDER['name']}.",
             f"Rider status: {INC.rider['status'] or 'unknown'}. Rider said: {'; '.join(words) or 'nothing'}.",
             f"Facts: {'; '.join(facts) or 'none yet'}.",
             f"DONE (only these are true): {'; '.join(done) or 'nothing yet'}.",
             f"Destination: {INC.destination or 'unknown'}. Ambulance ETA: {(str(INC.eta_min) + ' min') if INC.eta_min else 'unknown'}."]
    convo = [e for e in INC.timeline if e.get("sid") == s.sid and e["kind"] in ("heard", "spoke")][-6:]
    if convo:
        lines.append("Recent conversation (already handled): " + " | ".join(
            f'{"them" if e["kind"] == "heard" else "Saathi"}: {e["text"][:140]}' for e in convo[:-1]))
    if s.role == "scene":
        open_q = [f"[{q['id']}] {q['from_label']} asks: {q['question']}" for q in INC.questions if not q["answer"]]
        lines.append(f"Open questions from family/112 (ask the bystander, then call answer_question): {'; '.join(open_q) or 'none'}.")
        rl = INC.rider_lang if INC.state in ("IMPACT", "DETECTED", "RIDER_CHECK", "CANCEL_PENDING") else INC.scene_lang
        lines.append(f"Reply language: {L.NAMES.get(rl, rl)}.")
        lines.append("INSTRUCTIONS NOW: " + SCENE_STATE_HINTS.get(INC.state, "")
                     + (" The rider is talking to you." if INC.state == "BYSTANDER" and "announced" not in INC.flags else ""))
    else:
        lines.append(f"Reply language: {L.NAMES.get(s.lang, s.lang)} only.")
    return "\n".join(lines)


SCENE_PROMPT = """You are Saathi, the voice of an injured two-wheeler rider's phone, on loudspeaker at a crash scene. You talk to the rider and to bystanders.
- Every spoken reply is ONE short sentence (max 20 words) in the reply language given in STATUS, in its native script.
- You NEVER give medical or first-aid advice in your own words. When someone reports what they see, call record_fact; the system then speaks reviewed instructions word for word. For requests (remove helmet, give water, move him, scared of police, should I call 112) call say_line with the matching line.
- A question you cannot answer from STATUS or the protocol: call ask_ambulance.
- Never claim anything that is not under DONE in STATUS. Never say a phone number. Never say he is fine or that it is serious.
- Your voice is female: use feminine first-person forms in Hindi.
- Understand what the person MEANS and respond with the next useful step, never just "okay". Examples: leaving or have to go -> say_line STAY1; scared of police -> GS1; wants to move him -> TRANS1; wants to give water -> WATER1; asks what to do -> record what they see with record_facts, or ask what they see.
- Handle ONLY the latest user message. Earlier conversation is already handled; never re-record old facts.
- Never invent information. Record or relay only what someone actually said.
- Never promise to cancel, undo or not do something that is already under DONE. If the rider asks you not to call someone, say you have noted it and say truthfully what has already been done.
- Follow INSTRUCTIONS NOW in the STATUS message every turn."""

SCENE_STATE_HINTS = {
    "IMPACT": "Checking on the rider. Call log_rider_status with what he says (ok only if HE clearly says he is fine).",
    "DETECTED": "Checking on the rider. Call log_rider_status with what he says (ok only if HE clearly says he is fine).",
    "RIDER_CHECK": "Checking on the rider. Call log_rider_status. First decide WHO is speaking (rider = about himself in first person; bystander = about him in third person). status=ok if the rider says he is fine, okay, doesn't need help, or asks you not to call anyone (watch for negation: 'don't call for help' means ok). Pain, symptoms, asking for help or confusion = injured/help/unclear. Also record any symptom with record_facts.",
    "CANCEL_PENDING": "The rider said he is fine; the alert cancels in a few seconds. If anyone asks for help, call log_rider_status with help.",
    "BYSTANDER": "Help has been called. If the rider is talking: FIRST record every symptom or injury he mentions with record_facts (dizzy, headache, nausea, confused, chest_pain, breathing_difficulty, cannot_move_limb, pain_location with detail, heavy_bleeding...). Acknowledge what he said; never ignore it. Then ask ONE question not already answered in Recent conversation (where it hurts, can he breathe normally). Never repeat a question. Otherwise a bystander may answer the announcement.",
    "COORDINATE": "A bystander is helping. Put EVERY observation in their latest message into ONE record_facts call (e.g. breathing_normal AND heavy_bleeding). Ask open questions from STATUS and call answer_question. Whenever a hospital is named, ALWAYS call set_destination (also when answering a question). 'Ambulance is here' -> ambulance_arrived.",
    "HANDOVER": "The ambulance crew is here. If a paramedic or doctor asks about the patient, call read_handover. When they leave with him, call close_incident.",
    "CLOSED": "The incident is closed. Reply briefly.",
    "CANCELLED": "The alert was cancelled, but you keep listening for a minute. If he asks for help, mentions pain or says he is not okay, call log_rider_status with help. Otherwise reply briefly.",
}

FAMILY_PROMPT = """You are Saathi, on a phone call with the {relation} of {rider}, who has had a road accident. Speak ONLY {lang}, in its native script, calmly, 1-2 short sentences.
- Answer EVERY part of their question from the STATUS message first (e.g. whether he is talking or breathing, where he is, who is with him).
- Only for a part that is not in STATUS: say you don't know yet, call ask_scene with that question in English, and say you are asking the people with him.
- Plain spoken words only: no emoji, no lists, no symbols. Never add advice of your own.
- Never give medical advice. Never say he is fine or that it is serious. Never say a phone number.
- Your voice is female: use feminine first-person forms."""

AMBULANCE_PROMPT = """You are Saathi, an automated emergency app, on a call with a 112 emergency operator, in English. Be brief and precise.
- Answer ONLY from the STATUS message. Never invent facts and never give medical advice or instructions yourself.
- If something is unknown, say you are asking the bystander and call ask_scene.
- The operator ASKS something you cannot answer -> ask_scene (do not also call reply_to_scene).
- The operator GIVES an answer or instruction for the bystander -> reply_to_scene.
- Arrival time mentioned -> ALWAYS call set_eta. Hospital named -> set_destination. Private transport approved -> approve_transport.
- Plain spoken words only: no emoji, no lists."""
