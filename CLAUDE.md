# Saathi: context for Claude sessions

**What this is:** a two-wheeler crash voice responder for Bengaluru commuters. It's for Track 5 ("Voice AI for Bharat") at Build with Agora Bengaluru, **21 Nov 2026**. **Submission closes at 12:30 PM IST on Commudle**; finalist demos start at 3 PM.

**Read these first:**
- [docs/scenario_tree.md](docs/scenario_tree.md): every scenario, the timers, the language and offline plans, answers for judges
- [docs/hackathon_compliance.md](docs/hackathon_compliance.md): our build checked against the hackathon FAQ
- [docs/first_aid_protocol.md](docs/first_aid_protocol.md): the reviewed first-aid lines
- Background: the product brief and market study in `docs/`

## Non-negotiable design rules
- **Voice:** Agora ConvoAI, cascading Sarvam ASR → our LLM → Murf Falcon TTS. Started, spoken and stopped from the backend through REST.
- **LLM endpoint:** our own OpenAI-compatible `/llm/{sid}/chat/completions`, which runs the tool loop itself.
- **The backend owns a deterministic state machine.** The LLM only understands speech and picks tools.
- **First-aid and Good Samaritan lines** come only from `backend/protocol/first_aid.json`, spoken word for word through the `speak` API. The LLM never writes medical text.
- **Family phone numbers** never reach the LLM or any spoken line. **The medical profile** is read only from a template (`handover_en`).
- **112** is played by a teammate through a join link, never dialled. **The family** joins through a link (or SIP later).
- **Voices** follow Murf's recommended sheet:
  - scene: `en-IN-pooja` (speaks en, hi, kn, ta, te; it **cannot** speak Marathi);
  - family: chosen per language through `VOICE_BY_LANG` in `config.py` (Marathi → `gu-IN-diya`).

  All voices are female, so Hindi first-person lines use feminine verb forms.
- **Medical and language review is OPEN.** Present it as a prototype that gets sign-off before launch.

## Layout
```
backend/                FastAPI (Python 3.10+), run from backend/
  main.py               app, /dash, /j/{sid}, /session/* (compat with the current Android app)
  crash.py              /crash/impact|confirmed|cancel|simulate, /incident, /api/s/{sid}[/joined]
  workflow.py           STATE MACHINE + orchestration: sessions, timers, relays, briefings, handover, summary
  llm.py                per-session LLM endpoint: compact context (system + STATUS + latest message), tool loop
  tools.py              state-gated tool schemas and dispatcher
  protocol.py           facts -> protocol lines (FACT_LINES, priority, critical facts)
  llmclient.py          Groq 120b keys (round-robin) -> 20b keys -> Sarvam-105B, with 429 cooldown
  compose.py            restates NON-medical status text into another language (relays)
  lang.py               per-utterance language detection (script + Hindi/Marathi word cues)
  agora.py              ConvoAI REST (join/speak/leave/query/history) + RTC tokens (agora_token/ is Agora's official code)
  data/profile.json     demo rider "Rahul" (Marathi mother tongue; rider check in hi/en), contact: mother (Marathi)
  protocol/first_aid.json   41 lines x en/hi/kn, sources, what we deliberately don't say
  static/dash.html      incident dashboard; the laptop can act as the rider's phone
  static/join.html      join-link page for Mom / 112
  scripts/              check_keys.py, list_voices.py, render_protocol.py, smoke_workflow.py
android/                Kotlin app (com.saathi.app): on-device crash detector + live graph + Agora voice SDK 4.6.4
```

## Run it
1. **`.env` at the repo root.** Copy `.env.example`. Needs Agora App ID and Certificate, Customer ID and Secret, Murf, Sarvam, and `LLM_API_KEY` (plus optional `LLM_API_KEY_2..9` from *other* Groq accounts). **Never commit `.env`.**
2. **Backend:**
   ```
   cd backend && python -m venv .venv
   .venv/bin/pip install -r requirements.txt        # Windows: .venv\Scripts\pip
   .venv/bin/python -m uvicorn main:app --port 8000  # Windows: .venv\Scripts\python
   ```
3. **Tunnel** (Agora must reach `/llm`): `cloudflared tunnel --url http://localhost:8000`. Install with `brew install cloudflared` on Mac or `winget install Cloudflare.cloudflared` on Windows. Put the printed `https://….trycloudflare.com` into `.env` as `PUBLIC_BASE_URL`, then **restart the backend**. The URL changes on every tunnel restart.
4. **Dashboard:** open `PUBLIC_BASE_URL/dash` (the tunnel URL, so join links work on other phones). Click **Simulate crash + join**.
5. **Checks:**
   - `python scripts/check_keys.py`: live check of every key.
   - `python scripts/smoke_workflow.py`: the full workflow with the real LLM and a **fake Agora**, so no Agora minutes are used.
6. **Android:** a Gradle wrapper is included. Needs JDK 17 and the Android SDK (platform 35, build-tools 35); `android/local.properties` holds `sdk.dir`.
   - Build: `./gradlew assembleDebug`
   - Install: `adb install -r app/build/outputs/apk/debug/app-debug.apk`
   - The app's backend URL is baked in from `PUBLIC_BASE_URL` at build time, or can be typed into the app.

## Status (as of about 10:30 on 21 Nov)
- **Done and tested on a real phone (OPPO A5 2020):**
  - the voice pipeline;
  - on-device crash detection (impact > 2.5 g → still 2.5 s → tilt > 45°), with the agent pre-warmed at impact. Greeting 1.5 s after confirmation.
- **Backend workflow done:** passes `smoke_workflow.py` (fake Agora). **The live test with real Agora was next and hadn't been run yet.**
- **Android app not yet updated** for the new flow. Still to add:
  - an emergency screen card with a 20 s **I'm OK** button that calls the backend to cancel;
  - an SMS fallback with the location, plus the family link;
  - a profile and languages screen.

  The current app still works through `/crash/*` and `/session/*`.
- **Remaining before submission:** live test → app changes (if time) → backup video → submit on Commudle.

## Gotchas learned the hard way
- **Groq free tier:** 8,000 tokens per minute and 1,000 requests per day per model, per *account*. Extra keys from the same account share that limit.
- **Groq models make only one tool call per turn,** so tools that take several facts must accept a list (`record_facts`).
- **Sending the full chat history makes the model re-handle old turns and invent answers.** `llm.py` sends only the system prompt, STATUS and the latest message.
- **Background timers must be tied to their own incident.** A new crash calls `stop_all(previous)`, and `stop_all` never cancels the task that's running it.
- **Murf model string** is `falcon-2.1`; Murf's voices API accepts only `gen2` and `falcon-2.1`. **Agora can't change the TTS locale mid-session**, so each party gets its own session.
- **`speak` text limit is 512 bytes.** Kannada is about 3 bytes per character. `agora.split_for_speak` handles long text.
- **Speech recognition** is Sarvam, because Murf isn't an Agora ASR option. Agora doesn't pass Sarvam's detected-language code to the LLM, so `lang.py` detects it.
- **SIP calling to real phones is deferred.** It needs Agora's Preview `/v1 sessions` API, a saved agent, and a paid Twilio SIP trunk (details in scenario_tree.md section 12, item 5). The demo uses join links sent by SMS from the rider's phone.
- **About 300 free Agora ConvoAI minutes in total.** Each full test runs three agents. Stop agents after tests (dashboard: "Stop all agents").
- **Windows Git Bash:** use `PYTHONIOENCODING=utf-8` for Indic output. **ColorOS** blocks `pm grant`, so permissions must be accepted on the phone.
- **Repo:** github.com/varad394/Saathi. Work on `develop`, merge to `main` when it's demo-ready.
