# Saathi barebones plan: prove the pipeline end to end

**Goal:** prove one thing. The Android phone on loudspeaker talks to an Agora ConvoAI agent. Speech comes in through Sarvam (code-mixed kn/hi/en), goes to our FastAPI `/llm` endpoint, which runs one real tool call, and comes back out as Murf Falcon speech. The backend can also force a fixed line through `speak`. No sensors, no state machine, no family call yet.

**Done when** all six checks below pass on the OPPO A5 2020.

---

## 1. Shape

```
OPPO A5 (Android RTC SDK, speakerphone)            Laptop
  [Start] button ── POST /session/start ──────────▶ FastAPI :8000 ──▶ Agora ConvoAI REST /join
  joins channel "saathi-test" as uid 1001                │                 │
  ◀──────────── audio (RTC) ────────────▶  Agora agent uid 999             │
                                             ASR: sarvam (language "unknown")
                                             LLM: https://<tunnel>/llm/chat/completions ◀─┘
                                             TTS: murf FALCON, one voice
  [Speak fixed line] ── POST /session/speak ─▶ FastAPI ──▶ ConvoAI /speak
  [Stop] ── POST /session/stop ──────────────▶ FastAPI ──▶ ConvoAI /leave
```

## 2. Files (keep it to this)

```
backend/
  main.py          FastAPI: /token, /session/start|speak|update|stop, mounts llm router
  agora.py         REST client for join / speak / update / leave + RTC token builder
  llm.py           OpenAI-compatible /llm/chat/completions (SSE) with server-side tool loop
  tools.py         2 tools: get_crash_context(), log_rider_status(status, words)
  scripts/list_voices.py   lists Murf voices, filters for en-IN + hi-IN + kn-IN
android/            one Activity: Start / Speak fixed line / Stop, plus a status text
.env
```

Tool execution follows Agora's `recipe-agent-tool-calling` pattern. The tool loop runs **inside our /llm handler**, and only final text streams back to Agora. Agora's native `llm.tools` (which needs an https webhook) stays as plan B.

## 3. ConvoAI join payload (barebones)

`POST https://api.agora.io/api/conversational-ai-agent/v2/projects/{APP_ID}/join` · `Authorization: Basic base64(customer_id:customer_secret)`

```json
{
  "name": "saathi-<unix_ts>",
  "properties": {
    "channel": "saathi-test",
    "token": "<RTC token for uid 999>",
    "agent_rtc_uid": "999",
    "remote_rtc_uids": ["1001"],
    "idle_timeout": 60,
    "asr": { "vendor": "sarvam", "language": "en-IN",
             "params": { "api_key": "<SARVAM_API_KEY>", "language": "unknown" } },
    "llm": {
      "url": "https://<tunnel>/llm/chat/completions",
      "api_key": "<CUSTOM_LLM_SHARED_KEY>",
      "style": "openai",
      "system_messages": [{ "role": "system", "content": "You are Saathi... reply in the language the user spoke. One short sentence." }],
      "greeting_message": "Saathi here. Looks like you fell. Are you okay? / Neevu sari iddira? / Aap theek hain?",
      "failure_message": "Please wait, help is being called.",
      "max_history": 16,
      "params": { "model": "<LLM_MODEL>" }
    },
    "tts": { "vendor": "murf",
             "params": { "api_key": "<MURF_API_KEY>", "voiceId": "<MURF_VOICE_ID>", "locale": "en-IN",
                         "model": "falcon-2.1", "sample_rate": 24000 } },
    "turn_detection": { "mode": "default",
                        "config": { "end_of_speech": { "mode": "vad", "vad_config": { "silence_duration_ms": 640 } } } },
    "parameters": { "silence_config": { "timeout_ms": 10000, "action": "speak", "content": "Is anyone there? Please talk to me." } }
  }
}
```
Response: `{ "agent_id", "create_ts", "status" }`. Save `agent_id`.

- **speak:** `POST .../agents/{agent_id}/speak` with `{"text": "...", "priority": "INTERRUPT", "interruptable": false}`. Limit: **512 bytes** (Kannada script is about 3 bytes per character, so roughly 170 characters).
- **update:** `POST .../agents/{agent_id}/update` with `{"properties": {"llm": {"system_messages": [...], "params": {...}}}}`. Only `token`, `llm.system_messages` and `llm.params` are updatable, and `params` replaces the whole object. **TTS voice and locale can't be changed live.**
- **leave:** `POST .../agents/{agent_id}/leave`

## 4. Build steps (about 3 hours)

| # | Step | Proves | Time |
|---|---|---|---|
| 0 | Enable USB debugging on the phone, then `adb devices` shows it | device | 10 min |
| 1 | `.env` filled. `scripts/list_voices.py` picks one Falcon voice with en-IN, hi-IN and kn-IN | Murf key and voice | 15 min |
| 2 | FastAPI `/llm/chat/completions` streams SSE. Test with `curl -N` locally, including one tool call | LLM and tool loop | 40 min |
| 3 | Tunnel (`cloudflared tunnel --url http://localhost:8000`), then curl the public URL | Agora can reach us | 10 min |
| 4 | `/session/start` calls `/join` and returns `agent_id`. **Before Android**, join from a laptop browser (Agora Web demo or a tiny HTML page) to hear the agent | ConvoAI + Sarvam + Murf, separate from Android | 30 min |
| 5 | Android app: RTC SDK, `RECORD_AUDIO`, `setEnableSpeakerphone(true)`, join as uid 1001, Start/Speak/Stop buttons calling the backend | Android RTC on loudspeaker | 60 min |
| 6 | Run the checks below | everything | 20 min |

## 5. Pass/fail checks

1. Within about 2 s of tapping Start, the phone speaker plays the Murf greeting.
2. Say "I'm fine": the reply is in English.
3. Say "nanage kaalu novu aagthide" (Kannada): the reply is in Kannada, in the same voice.
4. Say "mera pair mein bahut dard hai, help karo" (Hindi-English mix): the reply is in Hindi, and the backend log shows a `log_rider_status` tool call.
5. Tap "Speak fixed line": the exact first-aid line is spoken word for word and interrupts the agent.
6. Tap Stop: the agent leaves, and `/leave` returns 200.

Log timestamps at tap, join 200, and first audio frame (`onFirstRemoteAudioFrame` on Android) to get real latency numbers for the full design.

## 6. Unverified assumptions (check during step 1, 2 or 4)

- **A1 (RESOLVED)** Murf model string is `falcon-2.1`: Murf's voices API says it accepts only `gen2` and `falcon-2.1`. Voice: started with `en-IN-nikhil` (en-IN, hi-IN, kn-IN); now `en-IN-pooja` per Murf's recommended-voices sheet, with per-language family voices — see scenario_tree.md section 1.6.
- **A2** A single Falcon voice speaks kn-IN when `locale` is set to `en-IN` and the text is in Kannada script. Since `locale` can't be changed through `update`, if this fails we need a per-language voice (one agent per language) or a different approach. **This is the top risk to test in step 4.**
- **A3** Sarvam `language: "unknown"` handles code-mixed input. The top-level `asr.language` versus `params.language` behaviour is undocumented. Agora doesn't return the detected language, so the LLM infers the reply language from the transcript text.
- **A4** Which Sarvam model Agora uses by default (and whether `params.model` passes through) is undocumented.
- **A5** Whether REST works with token auth alone (App ID + Certificate). Basic auth with Customer ID and Secret is documented, so we use that.
- **A6** `remote_rtc_uids` currently supports only one uid. That's fine for one phone on loudspeaker. The family call is a separate agent and channel.
- **A7** Outbound SIP (`POST .../call`) needs an Elastic SIP trunk (Twilio and similar) with Agora IPs allow-listed. That's out of the barebones scope.
