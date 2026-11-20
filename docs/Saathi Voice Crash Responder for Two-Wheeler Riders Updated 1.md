# Saathi: Voice Crash Responder for Two-Wheeler Riders

Nov 21, 2026 · @Varad

## Pitch

Saathi turns an office commuter's phone into a voice responder for the first 10 minutes after a two-wheeler crash. It detects the fall and uses the rider's last conscious seconds. Then it talks the people around him through calling his family and an ambulance, in their own language, without anyone unlocking the phone.

**Why we're building it.** A friend crashed his bike with his phone on him. He could speak for a few seconds, then lost consciousness. People nearby wanted to help but didn't know how to reach his family or what to tell them. His phone had emergency contacts, but every phone hides them in a different place. Help was standing right there, and the phone couldn't connect them to it.

## The problem

After a two-wheeler crash, the people nearby are usually willing to help but get stuck within the first minute. The same things break every time:

- **The rider's few seconds are wasted.** He may be able to talk for a moment, and whatever he says is lost.
- **The phone is locked.** Android and iPhone both have emergency information on the lock screen, but every brand puts it somewhere different. A panicking stranger won't find it.
- **Nobody knows what to say.** Even if someone reaches the family, they can't describe the exact location, what happened, or where he's being taken.
- **Languages don't match.** The bystander may speak Kannada, the family Hindi or Marathi, and the ambulance needs an exact location in any language.
- **People fear getting involved.** Many bystanders hold back because they worry about police questioning.
- **The hospital starts blind.** Doctors don't know his blood group, allergies, medicines, or when the crash happened.

This is a workflow, not a one-off event. Every crash runs the same steps: detect, check the rider, engage whoever is nearby, call family and an ambulance, guide first aid, hand over to the hospital. Today a stranger has to improvise all of it.

In 2023, two-wheeler riders were 44.8% of road deaths in India: 77,539 people (MoRTH, Road Accidents in India 2023).

## Target segment

**Primary: daily office commuters on two-wheelers in Bengaluru.** People who ride to work every day, often 30–90 minutes each way, on the Outer Ring Road, flyovers and tech-park routes. Many ride alone, early in the morning or late at night.

Why this group first:

- **The phone is on the rider.** Commuters keep the phone in a pocket or bag, so it stays with him after a fall. That is what lets Saathi hear his first few seconds and talk to people around him.
- **Data is on.** Urban commuters carry a smartphone with mobile data on throughout the ride, so the voice agent can work in real time.
- **The family is far away, and speaks another language.** Many Bengaluru commuters moved from other states. Their parents may speak Hindi, Marathi, Telugu or Bengali, while the people at the crash site speak Kannada.
- **This is our own story.** Our friend was exactly this rider.
- **Size:** \[number of daily two-wheeler commuters in Bengaluru, source, year\].

**What Saathi adds in a city.** In a city, an ambulance and bystanders usually arrive. What breaks is everything around them: the rider is alone when he falls, strangers can't reach his family, nobody shares a language, and the hospital starts without his history. Saathi fixes those gaps.

**Not our first target:** delivery and gig riders. Their phones are usually mounted on the handlebar, so after a crash the phone can be metres away from the rider. Some platforms already detect crashes and send an ambulance. We see them as a later expansion, built into the platforms' rider apps.

## Who it serves

The rider installs Saathi, but in a real crash the main user is a stranger standing next to him.

| Person | Their situation | What they need from Saathi |
| --- | --- | --- |
| Commuter, before any crash | Sets up once, rides the same route daily | A short profile, detection only during the commute, and no false alarms |
| Rider, just after the crash | May speak for seconds, or not at all | To be heard fast, and to cancel with "I'm fine" |
| Bystander | A stranger, scared, locked phone, maybe another language | Clear spoken steps, no unlocking, reassurance they won't get in trouble |
| Family | Gets an unexpected call | What happened, where, which hospital, said calmly in their language |
| Ambulance (112 / 108) | Needs to dispatch quickly | Exact location, conscious or not, breathing or not |
| Hospital staff | Receives an unknown patient | Blood group, allergies, medicines, crash time, what he said |

## How it works

Saathi runs in six stages, from the moment of the crash until the hospital takes over.

&#91;embedded content: crash response flow · 1 decision, 3 parallel actions\]

If the rider says he's fine, nothing else happens. Any other answer, or silence, starts the ambulance call, the family call and bystander guidance together.

1. **Setup, done once.** The rider adds name, blood group, allergies, conditions, medicines, emergency contacts, and the language each contact speaks.
2. **Detect.** The app watches the phone's motion only while the rider is moving at riding speed. A crash is three things together:
   - a sharp impact
   - a sudden change in the phone's orientation (the bike went down)
   - stillness afterwards, with speed dropping to zero
   - **Commute mode:** detection turns on only at riding speed, and by default only during the rider's usual commute hours. This saves battery and cuts false alarms.
3. **Check the rider (first \~20 seconds).** The phone speaks loudly in his language: "Saathi here. Looks like you fell. Are you okay?"
   - "I'm fine" cancels everything.
   - "Help", or any sign of pain, escalates at once. Saathi asks at most two quick questions ("Where does it hurt?", "Can you breathe?") and records the answers.
4. **Talk to bystanders.** If he doesn't answer, or stops answering, the phone switches to loudspeaker. It speaks in the local language, Hindi and English: "This rider has had an accident. I am his phone. Please talk to me. You don't need to unlock anything." It notices which language the bystander replies in and stays in that language.
5. **Coordinate, all at once.**
   - **Ambulance:** calls 112 or 108 with the location and what it knows so far.
   - **Family:** calls the emergency contacts in their own language. It tells them what happened, the exact location with a landmark, whether he was talking, and that an ambulance is called.
   - **Bystander:** guides them through fixed first-aid checks (breathing, bleeding, don't remove the helmet, don't move the neck).
   - **Reassurance:** tells the bystander that India's Good Samaritan law protects them.
6. **Update and hand over.** When the bystander says "the ambulance is here" or "they're taking him to Manipal", Saathi tells the family. When a paramedic or nurse asks "tell me about him", it reads out his medical profile and a short timeline: crash time, his words, what bystanders saw, who was called.

## Why voice

At a crash site, a screen fails and a voice works. Voice isn't a feature added on top; it's the only way a locked phone can ask strangers for help.

- **No unlocking, no menus.** The phone speaks first. Nobody has to find anything.
- **Hands stay free.** The bystander may be holding the rider's head or stopping traffic.
- **Every language in one conversation.** The bystander, the family and the ambulance may each speak a different language, and Saathi talks to each in theirs.
- **Works in panic and for people who can't read.** One spoken instruction at a time is easier than reading small text on a cracked screen.
- **A conversation, not a button.** An SOS button sends one fixed message. Saathi answers follow-up questions ("He's bleeding, what do I do?") and changes what it does based on the answers.
- **Speech becomes information.** The rider's last words and what bystanders saw become a summary the family and doctors can use.

## Safety and trust

An emergency product that gives wrong medical advice, or panics a family over a dropped phone, is worse than nothing. These rules are part of the design.

- **False alarms.** Detection is only switched on at riding speed. The rider gets a cancel window, and "I'm fine" stops everything. Family is called only after no response or a clear call for help. If a false alarm does reach family, Saathi calls back: "False alarm, he's okay."
- **No made-up medical advice.** First-aid guidance is a fixed script of standard bystander steps, reviewed by a medical professional before any real launch. The AI picks which line to say; it never writes new medical advice. Anything outside the script gets: "Please wait for the ambulance. I've already called them."
- **Only what is known.** Saathi tells family exactly what it knows and says "I don't know yet" for the rest. It never says "he's fine" or "it's serious".
- **Good Samaritan law.** Section 134A of the Motor Vehicles Act (added in 2019) protects people who help road accident victims, and they don't have to give their name. Saathi says this to the bystander early.
- **Privacy.** The medical profile is only read out in emergency mode, and only to responders who ask. Family phone numbers are never read out to strangers; Saathi makes the calls itself. Location goes only to the family and the ambulance.
- **Battery and network.** In emergency mode it calls the ambulance and family first, then everything else. If there's no data connection, it falls back to an SMS with the location.

## System design

There are three parts: an Android app on the rider's phone, a small backend, and the Agora voice agent. The implementation isn't decided yet; this is the shape.

- **Android app (the old phone in the demo)**
  - Runs in the background while riding and reads motion and GPS.
  - Decides on the phone itself that a crash happened, so detection works even on a weak network.
  - Keeps the screen and speaker on in emergency mode and carries the conversation through mic and loudspeaker.
  - Stores the rider's profile.
- **Backend**
  - Receives the crash event with location, impact data and the profile.
  - Runs the stages (rider check, bystander mode, calls, handover) and keeps the timeline.
  - Holds the fixed first-aid script and the rules for when to call whom.
- **Agora voice agent**
  - Joins the phone's audio and does speech-to-text, the language model and text-to-speech.
  - Its prompt includes the crash details, the profile, the current stage and the script it's allowed to use.
  - A second agent session (or the same agent) talks to the family on their call.
- **Calls out**
  - Family and ambulance calls need a way to ring a normal phone number. Ask the Agora team whether their agent can make outbound phone calls. If not, the demo sends family a link that joins them to the voice channel.
  - The SMS fallback with location works without the agent.

## Demo plan

The demo runs in about three minutes on the real Android phone, with a laptop showing live sensor readings and teammates playing the bystander, the mother and the paramedic.

1. **The story (30 s).** Tell the friend's story in four sentences. Ask him first.
2. **False alarm first (15 s).** Drop the phone, say "I'm fine", and it cancels. This answers the false-alarm question before anyone asks it.
3. **The crash (20 s).** Put the phone in a helmet or bag and drop it onto a mattress. The laptop graph shows the impact spike. The phone asks "Are you okay?" You say "my leg..." and then go silent.
4. **Bystander mode (60 s).** The phone announces itself on loudspeaker. A teammate answers in Kannada. Saathi switches to Kannada, asks about breathing and bleeding, says not to remove the helmet, and mentions the Good Samaritan law.
5. **The family call (30 s).** A second device playing "Mom" gets the call in Hindi: what happened, the location, that an ambulance is coming. The bystander says "they're taking him to Manipal", and Mom hears that update.
6. **Handover (20 s).** A teammate playing a paramedic says "tell me about him". Saathi reads out his blood group, allergies, crash time and his last words.

Record a backup video of the full run before presenting, in case the venue Wi-Fi fails. Tell judges that detection is tuned for the mattress drop, not proven on real crashes.

## What's different

Existing tools alert someone. Saathi coordinates the people who are actually at the scene.

- **Pixel and iPhone crash detection.** These only work on recent flagship phones, are designed mainly for car crashes, and call emergency services with an automated message. They don't hold a conversation with bystanders in Indian languages or guide them. Check their current availability in India before pitching.
- **SOS apps and shake-to-alert.** These send one fixed message with a location. Nobody at the scene gets help knowing what to do, and the family gets a pin with no context.
- **Built-in phone safety features.** Some commuters' phones already have crash or SOS features. Those send an alert. Saathi talks to the people standing next to the rider, and to his family, each in their own language. It can work alongside them.
- **Saathi.** Runs on a budget Android phone. Built for two-wheeler falls. Talks with the rider, then the bystander, then the family, each in their own language. Hands a usable summary to the hospital.

## Limits and future scope

The biggest open risk is detection accuracy: without real crash data, nobody can yet say how often it misses a crash or raises a false alarm.

**Known limits**

- **Detection is unproven.** The thresholds are hand-tuned. Real use needs crash data or partner testing.
- **Android may stop the app.** Many phone brands kill background apps to save battery, so riders would need to change battery settings for Saathi.
- **The phone may not survive.** It can break in the crash or land metres away from the rider.
- **Network gaps.** Highways often have weak coverage, so the SMS fallback matters.
- **The medical script needs review.** A doctor or trained first responder has to approve it before any real use.
- **Commuters must install it before they need it.** Safety apps are easy to forget. Commute mode and a free plan help, but adoption is unproven.
- **Who pays isn't proven.** Individual riders rarely pay for safety apps. We plan to test employers and insurers as payers.

**Where it could go**

- **Employers.** Companies with many two-wheeler commuters can offer Saathi free to employees as a safety benefit.
- **Insurers.** Two-wheeler and personal-accident insurers can bundle it with policies.
- **Delivery fleets.** Later, inside the rider apps of delivery platforms, once detection works for handlebar-mounted phones.
- **Hospital pre-alert.** Send the summary to the receiving hospital before the rider arrives.
- **Helmet or bike sensor.** A dedicated sensor for more reliable detection when the phone isn't on the rider.
- **Direct link to 112.** Integrate with India's emergency response system instead of placing a normal voice call.

## Judge questions

| Likely question | Short answer |
| --- | --- |
| How is this different from Pixel or iPhone crash detection? | Those are on flagship phones and send an automated alert. Saathi runs on budget Android and talks bystanders through what to do, in their language. |
| What about false alarms? | It only listens at riding speed, "I'm fine" cancels, and family is called only when there's no response or a clear call for help. |
| Isn't an AI giving medical advice dangerous? | Yes, which is why it doesn't. It can only choose from a fixed, reviewed first-aid script. |
| Why would a stranger trust a talking phone? | It opens with a clear purpose, never asks them to unlock anything, and tells them they're legally protected. |
| What if the phone breaks or there's no network? | Detection runs on the phone. Without data it falls back to an SMS with the location. A broken phone is a real limit, and a helmet sensor is the future fix. |
| Why voice AI and not just an SOS button? | The people at the scene need a back-and-forth conversation across languages. A button can't answer "he's bleeding, what do I do?" |
| Who pays? | Free for the rider. Employers pay to protect two-wheeler commuters, and insurers bundle it with policies. We still have to prove this. |
| Why commuters and not delivery riders? | A commuter's phone stays in his pocket, so it's with him after the crash. Delivery riders mount phones on the handlebar, and some platforms already send ambulances. They're our expansion. |
| In a city, won't an ambulance come anyway? | Usually, yes. What fails is reaching his family, sharing a language and briefing the hospital. That's what Saathi does. |
| How do you protect medical data? | The profile stays on the phone and is only read out in emergency mode, to responders who ask. |
