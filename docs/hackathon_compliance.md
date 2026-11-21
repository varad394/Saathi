# Saathi vs the Build with Agora rules

Checked against [buildwithagora - FAQ.md](buildwithagora%20-%20FAQ.md) (question numbers in brackets) on 21 Nov 2026, early morning.
Status: ✅ done and tested · 🟡 partly built · ❌ not built yet.

**Hard deadline: submit on Commudle by 12:30 PM today (Q22–23).** Mentors shortlist from 12:30 to 2:30. Finalists demo from 3:00 PM (Q27–29).

## 1. Mandatory requirements

| # | Rule (FAQ) | Status | Evidence in our build | Gap → action |
|---|---|---|---|---|
| 1 | Agora Conversational AI is a meaningful part of the solution (Q12, Q13, Q42) | ✅ | Cascading ConvoAI agent (Sarvam ASR → our LLM → Murf TTS). Started, spoken and stopped from our backend through the REST API (`join`, `speak`, `leave`, `history`). The rider's Android phone joins with the Agora RTC SDK in AI-client audio mode. The agent is pre-warmed at impact (greeting 1.5 s after confirmation). | Deepen with the family and 112 sessions (multi-agent, Q49) |
| 2 | Murf AI Falcon TTS for voice output (Q12, Q14, Q42) | ✅ | Every spoken word goes through Murf `falcon-2.1` as ConvoAI's TTS vendor. Voices follow **Murf's own recommended-voices sheet**: `en-IN-pooja` for the scene, plus the recommended voice per language for family calls. Offline clips are pre-rendered by Murf too. | — |
| 3 | Agentic workflow: tool calling or APIs that **perform actions**, not just answer (Q12, Q15, Q42) | 🟡 | Real LLM tool calls through our OpenAI-compatible endpoint (`log_rider_status`, `get_crash_context`). The backend starts and stops agents from phone events. | **The tools only record facts today.** Add action tools: `notify_family` (starts the family session and sends the link), `brief_ambulance` (112 session), `say_script_line`, `send_summary`. |
| 4 | Conversation in at least one Indian language supported by Murf Falcon; code-mixed encouraged (Q45, Q47) | ✅ | Hindi, Kannada and English, with code-mixed speech understood (tested: Hindi-English, Kannada). | — |
| 5 | **End-to-end service workflow through APIs** (Q45, Bharat minimum) | 🟡 | Crash → agent → conversation works end to end. | Crash → 112 briefing + family call + summary isn't connected yet. |
| 6 | End-to-end journey: **before, during, action, after** (Q42, Q43) | 🟡 | **Before:** profile and contacts are hard-coded. **During:** ✅. **Action:** 🟡 (row 3). **After:** ❌. | Before: show the rider's profile, contacts and languages (setup screen or profile file). After: family summary SMS, false-alarm callback, incident timeline. |
| 7 | Demo shows **initiate → understand/plan → execute → confirm → follow up** (Q44) | 🟡 | Initiate ✅ · understand ✅ · execute 🟡 · confirm ❌ · follow up ❌ | See section 2 |
| 8 | **Ask approval before critical actions**; handle errors gracefully (Q44, Q51) | 🟡 | Failure fallbacks exist (failure message, retry at confirmation, cancel on false alarm). | Approval needs an emergency-specific answer (section 3). |
| 9 | Working prototype and live demo; video only as backup (Q25, Q26, Q42) | 🟡 | Runs live on a real budget Android phone. | Record the backup video before 12:30. |

## 2. The five demo steps (Q44) mapped to Saathi

| FAQ step | What judges must see in Saathi | Status |
|---|---|---|
| 1 **Initiate**: the user speaks through Agora ConvoAI + Murf Falcon | The phone detects the crash and speaks first, in Kannada, Hindi and English. The rider answers. | ✅ |
| 2 **Understand / plan** | Code-mixed rider and bystander speech is understood. The agent decides: cancel, or escalate to ambulance + family + first aid. | ✅ understanding; 🟡 the state machine that plans next steps |
| 3 **Execute**: tools or APIs perform the task | Tool calls start the family session in Marathi, brief 112, and speak protocol lines through the `speak` API. | 🟡 |
| 4 **Confirm**: share the outcome, handle errors, approval for critical actions | After each action the agent tells the bystander what actually happened ("I've told his mother; the ambulance team has the location"). On failure it says so and uses the fallback (SMS). The approval gate is the rider check (section 3). | ❌ |
| 5 **Follow up**: update systems, send a summary, schedule next steps | It relays "taking him to Manipal" to the family, gives the paramedic handover, sends the family a summary SMS, and records the incident timeline. A false-alarm callback goes out if needed. | ❌ |

## 3. "Ask before critical actions" (Q51) in an emergency
An unconscious rider can't approve anything, so Saathi uses **announced, cancellable actions** (opt-out consent), plus explicit approval wherever someone *can* give it:

1. **The rider check is the approval gate.** "Saathi here. Looks like you fell. I'll call your family and an ambulance in 20 seconds unless you say you're fine." Saying "I'm fine" or tapping **I'm OK** cancels it. Silence is treated as not okay. *Action: add this sentence to the greeting.*
2. **The rider set this up in advance.** During setup he chose his contacts, their languages, and consent to share his medical profile in an emergency (DPDP Act s.7(f), medical-emergency exception).
3. **Moving the patient** needs the 112 operator's approval (`TRANS2` in the protocol).
4. **The medical profile** is read only to medical responders, from a template.
5. **Relaying the bystander's words to the family** is confirmed first: "Shall I tell his mother that?" *(stretch)*

Say this out loud in the demo. It answers Q51 before a judge asks.

## 4. Allowed and encouraged (no action needed)
- Other technologies and APIs are allowed (Q17): Sarvam ASR, Groq LLM and cloudflared are fine.
- RAG, MCP, memory and multiple agents are encouraged (Q49): the scene, family and 112 sessions count as multi-agent.
- Visual interfaces and physical devices are welcome (Q50): phone sensors plus the live accelerometer graph.
- Payments (Q48): not applicable.

## 5. Judging criteria (Q24) and where our evidence is

| Criterion | What to show or say |
|---|---|
| Problem–solution fit | The friend's story. Two-wheeler riders were 44.8 % of India's road deaths in 2023, and Bengaluru had 915 road deaths (55 % two-wheelers). The bystander's language and legal-fear problem. |
| Innovation | The phone talks to strangers. Facts are relayed across languages (Kannada bystander ↔ Marathi mother). The agent is pre-warmed at impact. Instructions are pre-recorded in the Murf voice for use offline. |
| Use of Agora and Murf | ConvoAI cascade with a custom tool-calling LLM; REST `join`, `speak`, `update`, `leave` and `history`; several concurrent agent sessions; the Android RTC SDK; Falcon voices chosen per language from Murf's recommendations. |
| Product functionality | The live run on a real budget phone. Measured: greeting **1.5 s** after the crash is confirmed, replies 0.5–0.8 s from the model. |
| Future scope, scalability | [scenario_tree.md](scenario_tree.md) section 12, plus employers and insurers as payers (from the brief). |

**Prize fit:**
- **Best Conversational AI Agent:** natural, low-latency voice that switches language mid-conversation.
- **Master Builder:** the working phone demo.
- **Breakthrough Innovation:** the multi-party relay and the bystander-first idea.

## 6. Logistics checklist
- [ ] Track 5 "Voice AI for Bharat" is selected on Commudle. The choice is final (Q6–7). *Confirm in your Commudle account.*
- [ ] Submit on Commudle **before 12:30 PM** (Q22–23): repo link, short description, backup video.
- [ ] Agora free tier is about **300 ConvoAI minutes** (Q16). Every test uses minutes for each session (scene + family + 112). Stop agents after each test, and keep `idle_timeout` short.
- [ ] Bring a government photo ID, laptop, charger (Q37). Demo kit: the OPPO phone and its USB cable, a mattress or bag, two teammate phones (Mom and 112), and a mobile hotspot in case venue Wi-Fi fails.
- [ ] Optional: share the Builder Pass and tag Agora and Murf AI.

## 7. Must-do before 12:30, in order
1. **State machine + approval gate**, including the "unless you say you're fine" greeting (rows 7–8).
2. **Action tools**: `notify_family`, `brief_ambulance`, `say_script_line` (rows 3, 5).
3. **Confirm step**: the agent states the real outcome of each action (section 2, step 4).
4. **Follow-up**: family summary SMS at handover, false-alarm callback (row 6, "after").
5. **Before**: show the profile, contacts and languages on the phone (row 6, "before").
6. **Backup video**, then submit.
