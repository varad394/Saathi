# Saathi demo video script (about 3 minutes)

## Cast and devices
| Who | Device | Role |
|---|---|---|
| **You (rider)** | The OPPO with the Saathi app, loudspeaker on, volume at max | Rider, then silent |
| **Teammate A** | Stands next to the OPPO | Bystander (Kannada; Hindi is fine if needed) |
| **Teammate B** | Phone 2, **Chrome**, headphones | Mom (Marathi; Hindi words are fine) |
| **Teammate C** | Phone 3, **Chrome**, headphones | 112 operator, then paramedic |
| **Camera** | A 4th phone filming the OPPO and the people | Records voices from the loudspeaker |
| **Laptop** | Dashboard at `PUBLIC_BASE_URL/dash`, screen-recorded (Win + Alt + R) | Shows the state machine live. **Don't click Join on it.** |

## Pre-flight (5 min)
1. **Laptop:** backend and tunnel running; dashboard open at the tunnel URL; reload it.
2. **OPPO:** Wi-Fi or data on; volume at max; Saathi app open.
   - **Settings:** Mom's phone = phone 2's number, 112 phone = phone 3's number. **Save.**
3. **Phones 2 and 3:** Chrome is the default browser, and the microphone is allowed for the tunnel site. If an SMS link opens inside the SMS app: **⋮ → Open in Chrome**.
4. **Phones 2 and 3 use headphones**, and Mom stands about 3 m away, so the phones don't hear each other.
5. **Dry run once** (it uses about 12 Agora minutes). Then record.

## The script

### Beat 1: false alarm (20 s) · *Track 5: initiate in an Indian language*
- **Caption:** "Saathi detects a fall. First, a false alarm."
- **OPPO:** tap **Simulate crash** (or *Arm detection* and drop it on a mattress so the graph spikes).
- **Saathi:** *"साथी बोल रही हूँ। आप ठीक हैं? … Saathi here. Are you okay?"*
- **You:** **"I'm fine."** (or tap **I'M OK**)
- **Saathi:** *"Okay, I am cancelling the alert. Say help if you need me."* The screen turns green, then the call ends after 60 s. Tap **End** to skip ahead.

### Beat 2: the crash (30 s) · *understand code-mixed speech*
- **Caption:** "A real crash. The rider can speak for a few seconds."
- **OPPO:** tap **Simulate crash**.
- **You (weakly):** **"मेरा सिर घूम रहा है… my leg hurts."**
- **Saathi:** *"मैं अभी आपके परिवार और एम्बुलेंस को बुला रही हूँ… Where does it hurt?"* Then *"Please stay lying down and keep still…"*
- **Show:** the screen turns red with *"Help is being called"*, the **SMS messages are sent** to phones 2 and 3, and **What Saathi has done** shows Ambulance and Family.
- **You:** **stay silent** (you've "passed out"). About 15 s later, Saathi announces on the loudspeaker in **Kannada → Hindi → English**: *"This rider has had an accident. I am his phone. Please talk to me…"*

### Beat 3: the bystander (45 s) · *assist*
- **Teammate A (Kannada):** **"ನಾನು ಇಲ್ಲಿದ್ದೀನಿ, ಅವನು ಮಾತಾಡ್ತಿಲ್ಲ."** *(naanu illiddeeni, avanu maataadtilla: "I'm here, he isn't talking")*
  - *Hindi alternative:* "मैं यहाँ हूँ, ये बोल नहीं रहे।"
- **Saathi (Kannada, word for word from the protocol):** the Good Samaritan line, then *"lift the visor… look at his chest for ten seconds…"*
- **Teammate A:** **"ಉಸಿರಾಡ್ತಿದ್ದಾನೆ, ಆದರೆ ಕಾಲಿನಿಂದ ತುಂಬಾ ರಕ್ತ ಬರ್ತಿದೆ."** *(usiraadtiddaane, aadre kaalininda tumba rakta bartide: "he's breathing, but a lot of blood from his leg")*
  - *Hindi alternative:* "साँस ले रहा है, पर पैर से बहुत खून बह रहा है।"
- **Saathi:** the bleeding instructions **interrupt** at once (*press hard with a cloth…*), then *"don't remove the helmet…"*
- **Teammate A:** **"ಹೆಲ್ಮೆಟ್ ತೆಗೆಯಲಾ?"** *(helmet tegeyala: "shall I remove the helmet?")* → *"Please do not take off his helmet…"*
- **Caption:** "Every first-aid line is a fixed, reviewed script. The AI only chooses which one."

### Beat 4: Mom and 112 (45 s) · *execute through tool calls*
- **Teammate C (phone 3):** open the **112 link** from the SMS in Chrome → **Tap to join**. Saathi briefs in English: location, GPS, blood group, *"bleeding heavily, someone pressing on the wound"*.
  - **C says:** **"Ambulance will reach in 8 minutes."** The OPPO announces the ETA in Kannada.
- **Teammate B (phone 2):** open the **Mom link** in Chrome → **Tap to join**. Saathi speaks **in Marathi**: what happened, where, that he was talking and now isn't, that he's bleeding, and that the ambulance is informed.
  - **B (Marathi) asks:** **"तो शुद्धीवर आहे का? कोणत्या हॉस्पिटलला नेणार?"** *(to shuddhivar aahe ka? kontya hospitalla nenaar: "is he conscious? which hospital?")*
  - Saathi answers what it knows, says it's asking the people with him, and **the OPPO asks the bystander in Kannada**.
- **Teammate A:** **"ಮಣಿಪಾಲ್ ಆಸ್ಪತ್ರೆಗೆ ಕರ್ಕೊಂಡು ಹೋಗ್ತಾರೆ."** *(Manipal aaspatrege karkondu hogtaare: "they're taking him to Manipal")* → **Mom hears it in Marathi.**
- **Caption:** "Kannada bystander ↔ Marathi mother. Saathi relays facts, not raw translation."

### Beat 5: handover (25 s) · *confirm and follow up*
- **Teammate C (now at the OPPO as the paramedic):** **"Ambulance has come."** → the screen turns blue: *"Ambulance team is here"*. Mom is told.
- **C:** **"I'm the paramedic. Tell me about him."** → Saathi reads the handover: name, blood group, allergies, crash time, his words, what was observed, first aid given, who was informed.
- **Laptop:** click **Close incident** → Mom hears the summary. The dashboard shows the full timeline.
- **Caption:** "Medical profile read from a template, never through the AI. Family numbers never spoken."

### Closing card (10 s)
"Saathi: on-device crash detection · Agora Conversational AI (ARES speech-to-text, custom tool-calling LLM, speak API, multiple agent sessions) · Murf Falcon voices · Kannada, Hindi, Marathi, English · works offline with SMS and stored Murf clips."

## If something goes wrong while recording
| Problem | Fix |
|---|---|
| Saathi doesn't hear you | Speak 30 cm from the phone; Settings → `speech_threshold` 0.65 |
| Room chatter is picked up | Settings → `speech_threshold` 0.8, `ains_mode` 2 |
| A link says "microphone not allowed" | Open it in Chrome; the page still plays Saathi listen-only |
| An SMS didn't arrive | Copy the link from the dashboard (**Calls** panel) and send it on WhatsApp |
| Stuck in a state | Tap **End** on the OPPO (or **Stop all agents** on the dashboard), then start again |
