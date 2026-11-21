"""End-to-end workflow test with the REAL LLM (Groq) and a FAKE Agora (no ConvoAI minutes used).

Drives the backend over ASGI exactly as Agora and the phone would, and prints what each call would have spoken.
Usage: .venv/Scripts/python scripts/smoke_workflow.py
"""
import asyncio
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import httpx  # noqa: E402

import agora  # noqa: E402
import config as C  # noqa: E402
import workflow as W  # noqa: E402

SPOKEN: list[tuple[str, str, str]] = []
_n = 0


async def fake_join(**kw):
    global _n
    _n += 1
    return {"agent_id": f"FAKE{_n}-{kw['name'].split('-')[2]}", "status": "RUNNING"}


async def fake_speak(agent_id, text, priority="APPEND", interruptable=True):
    SPOKEN.append((agent_id, priority, text))


async def fake_leave(agent_id):
    return {}


async def fake_query(agent_id):
    return {"status": "RUNNING"}


agora.join, agora.speak, agora.leave, agora.query = fake_join, fake_speak, fake_leave, fake_query
import settings as S  # noqa: E402
S._cur.update(rider_check_s=6, rider_silent_s=3, cancel_undo_s=2, announce_every_s=60, greeting_s=0)  # in memory only
W.STOP_DELAY_S = 1

import main  # noqa: E402

AUTH = {"Authorization": f"Bearer {C.CUSTOM_LLM_SHARED_KEY}"}


async def turn(cli, sid, text, history):
    history.append({"role": "user", "content": text})
    t = time.perf_counter()
    r = await cli.post(f"/llm/{sid}/chat/completions", headers=AUTH, json={"stream": True, "messages": history})
    out = ""
    for line in r.text.splitlines():
        if line.startswith("data:") and "[DONE]" not in line:
            out += json.loads(line[5:])["choices"][0]["delta"].get("content", "")
    history.append({"role": "assistant", "content": out})
    print(f"\n>>> [{sid.split('-', 1)[1]}] {text}\n    reply ({(time.perf_counter() - t) * 1000:.0f} ms): {out!r}   state={W.INC.state}")
    return out


def flush(label=""):
    if SPOKEN:
        print(f"    speak calls {label}:")
        for aid, pr, tx in SPOKEN:
            print(f"      -> {aid} [{pr}] {tx[:160]}")
        SPOKEN.clear()


async def main_():
    tr = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=tr, base_url="http://test", timeout=60) as cli:
        # ---------- Path 1: false alarm (C1)
        print("=" * 30, "PATH 1: rider says he is fine")
        await cli.post("/crash/simulate")
        scene = W.INC.scene().sid
        await turn(cli, scene, "I'm fine, I'm fine, nothing happened", [])
        await asyncio.sleep(W.CANCEL_UNDO_S + 1.5)
        print("    state after undo window:", W.INC.state)
        flush()

        # ---------- Path 2: full emergency
        print("\n" + "=" * 30, "PATH 2: crash, rider talks then goes silent, Kannada bystander, Marathi mother")
        await cli.post("/crash/simulate")
        scene = W.INC.scene().sid
        h = []
        await turn(cli, scene, "मेरा पैर... बहुत दर्द हो रहा है", h)
        await asyncio.sleep(1)
        fam = next(s.sid for s in W.INC.by_role("family"))
        amb = next(s.sid for s in W.INC.by_role("ambulance"))
        print("    sessions:", [(s.role, s.voice, s.locale, s.status) for s in W.INC.sessions.values()])
        print("    actions:", W.INC.actions)
        await asyncio.sleep(W.RIDER_SILENT_S + 2)  # rider goes silent -> announcement
        flush("(rider silent -> announcement)")
        await turn(cli, scene, "ಹೌದು, ನಾನು ಇಲ್ಲಿದ್ದೇನೆ. ಅವನು ಮಾತಾಡ್ತಿಲ್ಲ, ಕಣ್ಣು ತೆರೆಯುತ್ತಿಲ್ಲ.", h)  # he isn't talking, eyes closed
        await asyncio.sleep(2)
        flush("(engagement)")
        await turn(cli, scene, "ಉಸಿರಾಡ್ತಿದ್ದಾನೆ, ಆದರೆ ಕಾಲಿನಿಂದ ತುಂಬಾ ರಕ್ತ ಬರ್ತಿದೆ", h)  # breathing, but lots of blood from leg
        await asyncio.sleep(2)
        flush("(breathing + bleeding)")
        await cli.post(f"/api/s/{amb}/joined")
        await asyncio.sleep(3)
        flush("(112 joined)")
        await cli.post(f"/api/s/{fam}/joined")
        await asyncio.sleep(5)
        flush("(mother joined)")
        fh = []
        await turn(cli, fam, "तो शुद्धीवर आहे का? कोणत्या हॉस्पिटलला नेणार आहेत?", fh)  # conscious? which hospital?
        await asyncio.sleep(3)
        flush("(mother asks)")
        await turn(cli, scene, "ಮಣಿಪಾಲ್ ಆಸ್ಪತ್ರೆಗೆ ಕರ್ಕೊಂಡು ಹೋಗ್ತಾರೆ", h)  # they'll take him to Manipal hospital
        await asyncio.sleep(4)
        flush("(destination)")
        ah = []
        await turn(cli, amb, "Okay. Ambulance will reach in 8 minutes. Is he breathing?", ah)
        await asyncio.sleep(4)
        flush("(112 talks)")
        await turn(cli, scene, "Ambulance has come.", h)
        await turn(cli, scene, "I am the paramedic. Tell me about him.", h)
        await asyncio.sleep(2)
        flush("(handover)")
        await cli.post("/incident/close")
        await asyncio.sleep(4)
        flush("(close)")
        inc = (await cli.get("/incident")).json()
        print("\nFINAL state:", inc["state"], "| destination:", inc["destination"], "| eta:", inc["eta_min"])
        print("facts:", [(f["kind"], f["detail"]) for f in inc["facts"]])
        print("questions:", [(q["question"], q["answer"]) for q in inc["questions"]])
        print("summary:", inc["summary"])


asyncio.run(main_())
