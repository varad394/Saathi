# Saathi first-aid protocol (spoken word for word)

**Version 0.1-draft.** Generated from `backend/protocol/first_aid.json` by `backend/scripts/render_protocol.py`. Edit the JSON, not this file.

> **Review status**
> - **clinical review:** OPEN (prototype) - drafted from the guidelines listed below; to be signed off by a doctor or certified first-aid trainer before launch
> - **hi review:** OPEN (prototype) - native-speaker check before launch
> - **kn review:** OPEN (prototype) - native-speaker check before launch (the team does not read Kannada; the English line is the meaning)
> - **speaker gender:** female - all voices are female (scene en-IN-pooja; family voices from Murf's recommended list), so Hindi first-person verbs use feminine forms (rahi hoon / sakti)

Every line below is spoken through Agora's `speak` API exactly as written. The LLM only chooses *which* line (by ID); it never writes medical text. The English line is the source, and the Hindi and Kannada lines say the same thing. Node IDs (E0, E4a, …) refer to the tree in [scenario_tree.md](scenario_tree.md).

## Principles
1. One action per sentence. Short, plain words. A frightened stranger must be able to follow it while holding a wound.
2. Life threats first: not breathing, then heavy bleeding, then unconscious but breathing, then everything else.
3. Never move a crash victim unless there is immediate danger (fire, traffic) or the airway is at risk (vomiting).
4. Keep the helmet on. Lift the visor to see the face. Hands-only chest compressions do not need the helmet removed.
5. Only say what the reviewed lines say. Anything else gets HOLD and goes to the 112 operator.

## What Saathi deliberately does not say
| Not said | Why |
|---|---|
| Removing the helmet | Risk of worsening a neck injury. Guidance for lay helpers is to leave it on unless the airway cannot be managed any other way; we route that decision to the ambulance team. |
| Raising the injured limb or using pressure points to stop bleeding | Current first-aid guidelines do not recommend them (no evidence of benefit); firm direct pressure is the recommended method. |
| Improvised tourniquets | Guidelines support tourniquets for life-threatening limb bleeding when trained and a proper device is available; untrained improvised use can cause harm. We escalate to 112 instead (BLEED4). |
| Raising the legs for shock | Not advised when trauma is likely, as in a road crash. |
| Neck collars or splinting by bystanders | Routine use by first-aid providers is not recommended. |
| Giving water, sugar, tea or medicines | Risk of vomiting and choking; may delay surgery; drug interactions unknown. |
| Keys or anything in the hand or mouth during a fit | Common Indian myth; can break teeth or cause choking. |
| Toothpaste, oil, butter or ice on burns | Common home remedies that worsen burns; cool water for 20 minutes is recommended. |
| Mouth-to-mouth rescue breaths | Hands-only CPR is recommended for untrained lay rescuers and needs no helmet removal. |
| Any diagnosis or prognosis (he is fine / it is serious / he will survive) | Saathi only reports what it knows. |

## Scene lines

### `AN1` · node D1
*When:* Bystander mode starts; repeat every 20 s until someone answers · *Sources:* non-clinical · *Size:* en 102 B · hi 291 B · kn 257 B

- **en:** This rider has had an accident. I am his phone. Please talk to me. You do not need to unlock anything.
- **hi:** इस राइडर का एक्सीडेंट हुआ है। मैं इनका फ़ोन हूँ। कृपया मुझसे बात कीजिए। आपको फ़ोन अनलॉक करने की ज़रूरत नहीं है।
- **kn:** ಈ ಸವಾರರಿಗೆ ಅಪಘಾತವಾಗಿದೆ. ನಾನು ಅವರ ಫೋನ್. ದಯವಿಟ್ಟು ನನ್ನ ಜೊತೆ ಮಾತಾಡಿ. ಫೋನ್ ಅನ್‌ಲಾಕ್ ಮಾಡುವ ಅಗತ್ಯವಿಲ್ಲ.

### `GS1` · node D5
*When:* Right after the first bystander reply, and whenever they sound afraid · *Sources:* GSR · *Size:* en 155 B · hi 430 B · kn 364 B

- **en:** You will not get into trouble for helping. You do not have to give your name. No one can force you to be a witness, and the hospital cannot ask you to pay.
- **hi:** मदद करने पर आप किसी मुसीबत में नहीं पड़ेंगे। आपको अपना नाम बताने की ज़रूरत नहीं है। कोई आपको गवाह बनने के लिए मजबूर नहीं कर सकता, और अस्पताल आपसे पैसे नहीं माँग सकता।
- **kn:** ಸಹಾಯ ಮಾಡಿದರೆ ನಿಮಗೆ ಯಾವುದೇ ತೊಂದರೆ ಆಗುವುದಿಲ್ಲ. ನಿಮ್ಮ ಹೆಸರು ಹೇಳುವ ಅಗತ್ಯವಿಲ್ಲ. ಸಾಕ್ಷಿಯಾಗಲು ಯಾರೂ ಒತ್ತಾಯಿಸುವಂತಿಲ್ಲ, ಆಸ್ಪತ್ರೆ ಹಣ ಕೇಳುವಂತಿಲ್ಲ.

### `HOLD` · node E-OUT
*When:* Any question outside this protocol; the question is relayed to the 112 operator · *Sources:* non-clinical · *Size:* en 82 B · hi 263 B · kn 332 B

- **en:** I can't advise on that. Please keep him still. I am asking the ambulance team now.
- **hi:** मैं इस बारे में सलाह नहीं दे सकती। कृपया इन्हें हिलने मत दीजिए। मैं अभी एम्बुलेंस टीम से पूछ रही हूँ।
- **kn:** ಅದರ ಬಗ್ಗೆ ನಾನು ಸಲಹೆ ಕೊಡಲು ಆಗುವುದಿಲ್ಲ. ದಯವಿಟ್ಟು ಅವರು ಅಲುಗಾಡದಂತೆ ನೋಡಿಕೊಳ್ಳಿ. ನಾನು ಈಗಲೇ ಆಂಬ್ಯುಲೆನ್ಸ್ ತಂಡವನ್ನು ಕೇಳುತ್ತಿದ್ದೇನೆ.

### `ASK112` · node F4
*When:* 112 track failed, or offline mode · *Sources:* IFAM · *Size:* en 68 B · hi 192 B · kn 222 B

- **en:** If you have a phone, please call 112. It works even without balance.
- **hi:** अगर आपके पास फ़ोन है, तो कृपया 112 पर कॉल कीजिए। यह बिना बैलेंस के भी लगता है।
- **kn:** ನಿಮ್ಮ ಬಳಿ ಫೋನ್ ಇದ್ದರೆ, ದಯವಿಟ್ಟು 112 ಗೆ ಕರೆ ಮಾಡಿ. ಬ್ಯಾಲೆನ್ಸ್ ಇಲ್ಲದಿದ್ದರೂ ಕರೆ ಹೋಗುತ್ತದೆ.

## Scene safety

### `SAFE1` · node E0
*When:* First first-aid step, briefly · *Sources:* ERC2021, IFAM · *Size:* en 104 B · hi 246 B · kn 259 B

- **en:** First, stay safe. Ask someone to warn and slow down the traffic. Do not stand in the middle of the road.
- **hi:** पहले अपनी सुरक्षा देखिए। किसी से कहिए कि ट्रैफ़िक को धीमा करवाए। सड़क के बीच में मत खड़े होइए।
- **kn:** ಮೊದಲು ನೀವು ಸುರಕ್ಷಿತವಾಗಿರಿ. ವಾಹನಗಳನ್ನು ನಿಧಾನ ಮಾಡಿಸಲು ಯಾರಿಗಾದರೂ ಹೇಳಿ. ರಸ್ತೆಯ ಮಧ್ಯದಲ್ಲಿ ನಿಲ್ಲಬೇಡಿ.

### `SAFE2` · node E0
*When:* Bike engine running, fire or petrol smell reported · *Sources:* IFAM · *Size:* en 100 B · hi 252 B · kn 264 B

- **en:** If the bike's engine is running, switch it off. If you see fire or smell petrol, move everyone back.
- **hi:** अगर बाइक का इंजन चालू है, तो उसे बंद कर दीजिए। अगर आग दिखे या पेट्रोल की गंध आए, तो सबको पीछे हटाइए।
- **kn:** ಬೈಕ್ ಎಂಜಿನ್ ಚಾಲೂ ಇದ್ದರೆ ಅದನ್ನು ಆಫ್ ಮಾಡಿ. ಬೆಂಕಿ ಕಂಡರೆ ಅಥವಾ ಪೆಟ್ರೋಲ್ ವಾಸನೆ ಬಂದರೆ, ಎಲ್ಲರನ್ನೂ ದೂರ ಸರಿಸಿ.

### `SAFE3` · node E0
*When:* Bystander wants to move him · *Sources:* ERC2021, IFRC2020 · *Size:* en 61 B · hi 135 B · kn 174 B

- **en:** Do not move him, unless he is in danger from fire or traffic.
- **hi:** जब तक आग या ट्रैफ़िक से ख़तरा न हो, इन्हें मत हिलाइए।
- **kn:** ಬೆಂಕಿ ಅಥವಾ ವಾಹನಗಳಿಂದ ಅಪಾಯ ಇಲ್ಲದಿದ್ದರೆ, ಅವರನ್ನು ಅಲ್ಲಿಂದ ಸರಿಸಬೇಡಿ.

### `PIN1` · node E12
*When:* Bike is lying on the rider · *Sources:* IFAM · *Size:* en 90 B · hi 218 B · kn 195 B

- **en:** If the bike is lying on him, lift the bike off with help from others. Do not pull him out.
- **hi:** अगर बाइक इनके ऊपर गिरी है, तो दूसरों की मदद से बाइक उठाइए। इन्हें खींचकर मत निकालिए।
- **kn:** ಬೈಕ್ ಅವರ ಮೇಲೆ ಬಿದ್ದಿದ್ದರೆ, ಬೇರೆಯವರ ಸಹಾಯದಿಂದ ಬೈಕ್ ಎತ್ತಿ. ಅವರನ್ನು ಎಳೆಯಬೇಡಿ.

## Assessment

### `RESP1` · node E1
*When:* Responsiveness check · *Sources:* ERC2021 · *Size:* en 92 B · hi 260 B · kn 275 B

- **en:** Talk to him loudly and tap his shoulders. Do not shake him. Does he answer or open his eyes?
- **hi:** इनसे ज़ोर से बात कीजिए और कंधे थपथपाइए। इन्हें झकझोरिए मत। क्या ये जवाब देते हैं या आँखें खोलते हैं?
- **kn:** ಅವರ ಜೊತೆ ಜೋರಾಗಿ ಮಾತಾಡಿ, ಭುಜ ತಟ್ಟಿ. ಅವರನ್ನು ಅಲುಗಾಡಿಸಬೇಡಿ. ಅವರು ಉತ್ತರ ಕೊಡುತ್ತಾರಾ ಅಥವಾ ಕಣ್ಣು ತೆರೆಯುತ್ತಾರಾ?

### `VISOR1` · node E1
*When:* Full-face helmet; before the breathing check · *Sources:* IFAM · *Size:* en 76 B · hi 185 B · kn 170 B

- **en:** You can lift the helmet's visor to see his face. Do not take the helmet off.
- **hi:** चेहरा देखने के लिए आप हेलमेट का शीशा ऊपर कर सकते हैं। हेलमेट मत उतारिए।
- **kn:** ಮುಖ ಕಾಣಲು ಹೆಲ್ಮೆಟ್‌ನ ಗಾಜನ್ನು ಮೇಲೆತ್ತಬಹುದು. ಹೆಲ್ಮೆಟ್ ತೆಗೆಯಬೇಡಿ.

### `BREATH1` · node E2
*When:* Unresponsive · *Sources:* ERC2021, AHA2020 · *Size:* en 75 B · hi 181 B · kn 194 B

- **en:** Look at his chest for up to ten seconds. Is it rising and falling normally?
- **hi:** दस सेकंड तक इनकी छाती देखिए। क्या वह सामान्य रूप से ऊपर-नीचे हो रही है?
- **kn:** ಹತ್ತು ಸೆಕೆಂಡ್ ಅವರ ಎದೆಯನ್ನು ನೋಡಿ. ಅದು ಸಾಮಾನ್ಯವಾಗಿ ಮೇಲೆ ಕೆಳಗೆ ಆಗುತ್ತಿದೆಯಾ?

### `BREATH2` · node E2
*When:* Bystander unsure, or describes gasping · *Sources:* ERC2021, AHA2020 · *Size:* en 54 B · hi 135 B · kn 136 B

- **en:** Gasping or very slow breaths are not normal breathing.
- **hi:** हाँफना या बहुत धीमी साँस लेना सामान्य साँस नहीं है।
- **kn:** ಏದುಸಿರು ಅಥವಾ ತುಂಬಾ ನಿಧಾನ ಉಸಿರು ಸಾಮಾನ್ಯ ಉಸಿರಾಟವಲ್ಲ.

## Not breathing: hands-only CPR

### `CPR0` · node E3
*When:* Not breathing normally AND lying face down or on his side · *Sources:* ERC2021 · *Size:* en 127 B · hi 291 B · kn 302 B

- **en:** He must be on his back on firm ground. With others, roll him over together, keeping his head, neck and body in a straight line.
- **hi:** इन्हें सख़्त ज़मीन पर पीठ के बल होना चाहिए। दूसरों के साथ मिलकर इन्हें पलटिए, सिर, गर्दन और शरीर एक सीध में रखिए।
- **kn:** ಅವರು ಗಟ್ಟಿ ನೆಲದ ಮೇಲೆ ಬೆನ್ನಿನ ಮೇಲೆ ಮಲಗಿರಬೇಕು. ಬೇರೆಯವರ ಜೊತೆ ಸೇರಿ, ತಲೆ, ಕುತ್ತಿಗೆ, ದೇಹ ನೇರವಾಗಿರುವಂತೆ ಅವರನ್ನು ತಿರುಗಿಸಿ.

### `CPR1` · node E3
*When:* Not breathing normally; also triggers PRIORITY re-brief to 112 · *Sources:* ERC2021, AHA2020 · *Size:* en 122 B · hi 319 B · kn 303 B

- **en:** Start chest pushes now. Kneel beside him. Put the heel of one hand on the centre of his chest, and your other hand on top.
- **hi:** अभी छाती दबाना शुरू कीजिए। इनके बगल में घुटनों पर बैठिए। एक हथेली का निचला हिस्सा छाती के बीच में रखिए, दूसरा हाथ उसके ऊपर।
- **kn:** ಈಗಲೇ ಎದೆ ಒತ್ತಲು ಶುರು ಮಾಡಿ. ಅವರ ಪಕ್ಕದಲ್ಲಿ ಮಂಡಿಯೂರಿ. ಒಂದು ಅಂಗೈಯ ಕೆಳಭಾಗವನ್ನು ಎದೆಯ ಮಧ್ಯದಲ್ಲಿ ಇಡಿ, ಇನ್ನೊಂದು ಕೈ ಅದರ ಮೇಲೆ.

### `CPR2` · node E3
*When:* Directly after CPR1 · *Sources:* ERC2021, AHA2020 · *Size:* en 138 B · hi 317 B · kn 324 B

- **en:** Keep your arms straight. Push down hard, about five centimetres, then let the chest come back up. Push fast, about two times every second.
- **hi:** हाथ सीधे रखिए। ज़ोर से लगभग पाँच सेंटीमीटर नीचे दबाइए, फिर छाती को ऊपर आने दीजिए। तेज़ी से दबाइए, हर सेकंड में लगभग दो बार।
- **kn:** ಕೈಗಳನ್ನು ನೇರವಾಗಿಡಿ. ಸುಮಾರು ಐದು ಸೆಂಟಿಮೀಟರ್ ಜೋರಾಗಿ ಒತ್ತಿ, ನಂತರ ಎದೆ ಮೇಲೆ ಬರಲು ಬಿಡಿ. ಸೆಕೆಂಡಿಗೆ ಸುಮಾರು ಎರಡು ಬಾರಿ ವೇಗವಾಗಿ ಒತ್ತಿ.

### `CPR3` · node E3
*When:* Directly after CPR2; repeat every 2 minutes · *Sources:* ERC2021, AHA2020 · *Size:* en 131 B · hi 273 B · kn 316 B

- **en:** Do not stop until the ambulance team takes over, or he starts breathing normally. If someone else is there, swap every two minutes.
- **hi:** जब तक एम्बुलेंस टीम न संभाले या ये ठीक से साँस न लेने लगें, रुकिए मत। कोई और हो, तो हर दो मिनट में बदल लीजिए।
- **kn:** ಆಂಬ್ಯುಲೆನ್ಸ್ ತಂಡ ಬರುವವರೆಗೆ ಅಥವಾ ಅವರು ಸರಿಯಾಗಿ ಉಸಿರಾಡುವವರೆಗೆ ನಿಲ್ಲಿಸಬೇಡಿ. ಬೇರೆಯವರಿದ್ದರೆ ಎರಡು ನಿಮಿಷಕ್ಕೊಮ್ಮೆ ಬದಲಾಯಿಸಿ.

### `CPR4` · node E3
*When:* Bystander asks about the helmet during CPR · *Sources:* AHA2020, IFAM · *Size:* en 66 B · hi 187 B · kn 159 B

- **en:** Keep the helmet on. You do not need to remove it for chest pushes.
- **hi:** हेलमेट पहना रहने दीजिए। छाती दबाने के लिए उसे उतारने की ज़रूरत नहीं है।
- **kn:** ಹೆಲ್ಮೆಟ್ ಹಾಗೆಯೇ ಇರಲಿ. ಎದೆ ಒತ್ತಲು ಅದನ್ನು ತೆಗೆಯುವ ಅಗತ್ಯವಿಲ್ಲ.

## Bleeding

### `BLEED1` · node E4
*When:* After breathing is confirmed, or for a conscious rider · *Sources:* ERC2021 · *Size:* en 39 B · hi 105 B · kn 103 B

- **en:** Is blood flowing heavily from anywhere?
- **hi:** क्या कहीं से बहुत ज़्यादा ख़ून बह रहा है?
- **kn:** ಎಲ್ಲಿಂದಾದರೂ ತುಂಬಾ ರಕ್ತ ಹರಿಯುತ್ತಿದೆಯಾ?

### `BLEED2` · node E4a
*When:* Heavy bleeding reported · *Sources:* ERC2021, IFRC2020, IFAM · *Size:* en 119 B · hi 247 B · kn 294 B

- **en:** Press hard on the wound with a clean cloth, like a handkerchief, dupatta or shirt. If there is no cloth, use your hand.
- **hi:** घाव पर किसी साफ़ कपड़े से ज़ोर से दबाइए, जैसे रूमाल, दुपट्टा या शर्ट। कपड़ा न हो तो हाथ से दबाइए।
- **kn:** ಗಾಯದ ಮೇಲೆ ಸ್ವಚ್ಛ ಬಟ್ಟೆಯಿಂದ ಜೋರಾಗಿ ಒತ್ತಿ, ಕರವಸ್ತ್ರ, ದುಪಟ್ಟಾ ಅಥವಾ ಶರ್ಟ್ ಆಗಬಹುದು. ಬಟ್ಟೆ ಇಲ್ಲದಿದ್ದರೆ ಕೈಯಿಂದ ಒತ್ತಿ.

### `BLEED3` · node E4a
*When:* Directly after BLEED2 · *Sources:* ERC2021, IFRC2020 · *Size:* en 133 B · hi 278 B · kn 300 B

- **en:** Keep pressing hard without stopping. Do not lift the cloth to check. If blood soaks through, add more cloth on top and keep pressing.
- **hi:** बिना रुके ज़ोर से दबाते रहिए। देखने के लिए कपड़ा मत हटाइए। ख़ून बाहर आए, तो ऊपर और कपड़ा रखिए और दबाते रहिए।
- **kn:** ನಿಲ್ಲಿಸದೆ ಜೋರಾಗಿ ಒತ್ತುತ್ತಲೇ ಇರಿ. ನೋಡಲು ಬಟ್ಟೆ ತೆಗೆಯಬೇಡಿ. ರಕ್ತ ಹೊರಬಂದರೆ, ಮೇಲೆ ಇನ್ನಷ್ಟು ಬಟ್ಟೆ ಇಟ್ಟು ಒತ್ತುತ್ತಲೇ ಇರಿ.

### `BLEED4` · node E4a
*When:* Bleeding not stopping despite pressure; also PRIORITY to 112 · *Sources:* ERC2021 · *Size:* en 81 B · hi 238 B · kn 278 B

- **en:** Keep pressing as hard as you can. I am telling the ambulance team this is urgent.
- **hi:** जितना हो सके उतना ज़ोर से दबाते रहिए। मैं एम्बुलेंस टीम को बता रही हूँ कि यह बहुत ज़रूरी है।
- **kn:** ಎಷ್ಟು ಸಾಧ್ಯವೋ ಅಷ್ಟು ಜೋರಾಗಿ ಒತ್ತುತ್ತಲೇ ಇರಿ. ಇದು ತುರ್ತು ಎಂದು ನಾನು ಆಂಬ್ಯುಲೆನ್ಸ್ ತಂಡಕ್ಕೆ ತಿಳಿಸುತ್ತಿದ್ದೇನೆ.

## Unconscious but breathing

### `UNC1` · node E5
*When:* Unresponsive but breathing normally · *Sources:* ERC2021, IFAM · *Size:* en 125 B · hi 269 B · kn 301 B

- **en:** He is breathing. Do not take off his helmet, and do not move his head or neck. Stay with him and keep watching his breathing.
- **hi:** ये साँस ले रहे हैं। हेलमेट मत उतारिए, और सिर या गर्दन मत हिलाइए। इनके पास रहिए और इनकी साँस पर नज़र रखिए।
- **kn:** ಅವರು ಉಸಿರಾಡುತ್ತಿದ್ದಾರೆ. ಹೆಲ್ಮೆಟ್ ತೆಗೆಯಬೇಡಿ, ತಲೆ ಅಥವಾ ಕುತ್ತಿಗೆ ಅಲ್ಲಾಡಿಸಬೇಡಿ. ಅವರ ಜೊತೆ ಇದ್ದು ಉಸಿರಾಟ ಗಮನಿಸುತ್ತಿರಿ.

### `UNC2` · node E5
*When:* Re-check every 2 minutes while unresponsive · *Sources:* ERC2021 · *Size:* en 31 B · hi 91 B · kn 100 B

- **en:** Is he still breathing normally?
- **hi:** क्या ये अब भी ठीक से साँस ले रहे हैं?
- **kn:** ಅವರು ಈಗಲೂ ಸರಿಯಾಗಿ ಉಸಿರಾಡುತ್ತಿದ್ದಾರಾ?

### `VOMIT1` · node E5a
*When:* Vomiting or gurgling reported · *Sources:* ERC2021, IFRC2020, IFAM · *Size:* en 100 B · hi 274 B · kn 311 B

- **en:** If he is vomiting or making gurgling sounds, turn him onto his side. Do it with two or three people.
- **hi:** अगर ये उल्टी कर रहे हैं या गले से गड़गड़ की आवाज़ आ रही है, तो इन्हें करवट पर कीजिए। दो-तीन लोग मिलकर कीजिए।
- **kn:** ಅವರು ವಾಂತಿ ಮಾಡುತ್ತಿದ್ದರೆ ಅಥವಾ ಗಂಟಲಿನಿಂದ ಗುರುಗುರು ಸದ್ದು ಬರುತ್ತಿದ್ದರೆ, ಎರಡು-ಮೂರು ಜನ ಸೇರಿ ಅವರನ್ನು ಒಂದು ಬದಿಗೆ ತಿರುಗಿಸಿ.

### `VOMIT2` · node E5a
*When:* Directly after VOMIT1 · *Sources:* ERC2021, IFAM · *Size:* en 86 B · hi 179 B · kn 197 B

- **en:** Keep his head, neck and body in one straight line as you turn him. Keep the helmet on.
- **hi:** पलटते समय सिर, गर्दन और शरीर एक सीध में रखिए। हेलमेट पहना रहने दीजिए।
- **kn:** ತಿರುಗಿಸುವಾಗ ತಲೆ, ಕುತ್ತಿಗೆ ಮತ್ತು ದೇಹ ಒಂದೇ ನೇರದಲ್ಲಿರಲಿ. ಹೆಲ್ಮೆಟ್ ತೆಗೆಯಬೇಡಿ.

## Conscious rider

### `RIDER_STILL` · node E6
*When:* The rider himself reports a symptom (dizzy, headache, nausea, confusion, chest pain, can't move a limb) · *Sources:* ERC2021, IFAM · *Size:* en 114 B · hi 307 B · kn 320 B

- **en:** Please stay lying down and keep still. Don't try to get up. Help is on the way, and I'm telling them how you feel.
- **hi:** कृपया लेटे रहिए और हिलिए मत। उठने की कोशिश मत कीजिए। मदद आ रही है, और मैं उन्हें बता रही हूँ कि आप कैसा महसूस कर रहे हैं।
- **kn:** ದಯವಿಟ್ಟು ಮಲಗಿಯೇ ಇರಿ, ಅಲುಗಾಡಬೇಡಿ. ಏಳಲು ಪ್ರಯತ್ನಿಸಬೇಡಿ. ಸಹಾಯ ಬರುತ್ತಿದೆ, ನಿಮಗೆ ಹೇಗನಿಸುತ್ತಿದೆ ಎಂದು ಅವರಿಗೆ ತಿಳಿಸುತ್ತಿದ್ದೇನೆ.

### `CONS1` · node E6
*When:* Rider is responsive · *Sources:* ERC2021, IFAM · *Size:* en 70 B · hi 150 B · kn 176 B

- **en:** Tell him to lie still and not to get up. Ask him not to move his head.
- **hi:** इनसे कहिए कि लेटे रहें और उठें नहीं। सिर न हिलाने को कहिए।
- **kn:** ಅಲುಗಾಡದೆ ಮಲಗಿರಲು, ಏಳದಿರಲು ಅವರಿಗೆ ಹೇಳಿ. ತಲೆ ಅಲ್ಲಾಡಿಸಬೇಡಿ ಎಂದು ಹೇಳಿ.

### `CONS2` · node E6
*When:* Directly after CONS1 · *Sources:* ERC2021, IFAM · *Size:* en 107 B · hi 236 B · kn 236 B

- **en:** Do not give him anything to eat or drink. Cover him with a cloth to keep him warm, and keep talking to him.
- **hi:** इन्हें खाने-पीने को कुछ मत दीजिए। गर्म रखने के लिए कपड़े से ढक दीजिए, और इनसे बात करते रहिए।
- **kn:** ಅವರಿಗೆ ತಿನ್ನಲು ಅಥವಾ ಕುಡಿಯಲು ಏನೂ ಕೊಡಬೇಡಿ. ಬೆಚ್ಚಗಿರಲು ಬಟ್ಟೆ ಹೊದಿಸಿ, ಅವರ ಜೊತೆ ಮಾತಾಡುತ್ತಿರಿ.

### `CONS3` · node E6
*When:* After CONS2; answer is recorded word for word · *Sources:* non-clinical · *Size:* en 30 B · hi 104 B · kn 126 B

- **en:** Please ask him where it hurts.
- **hi:** कृपया इनसे पूछिए कि दर्द कहाँ हो रहा है।
- **kn:** ಎಲ್ಲಿ ನೋವಾಗುತ್ತಿದೆ ಎಂದು ದಯವಿಟ್ಟು ಅವರನ್ನು ಕೇಳಿ.

## Other injuries

### `FRAC1` · node E7
*When:* Limb looks bent or bone is visible · *Sources:* ERC2021, IFAM · *Size:* en 107 B · hi 285 B · kn 262 B

- **en:** Do not try to straighten an injured arm or leg. Leave it as it is. Cover any open wound with a clean cloth.
- **hi:** चोट लगे हाथ या पैर को सीधा करने की कोशिश मत कीजिए। जैसा है वैसा रहने दीजिए। खुले घाव को साफ़ कपड़े से ढक दीजिए।
- **kn:** ಗಾಯಗೊಂಡ ಕೈ ಅಥವಾ ಕಾಲನ್ನು ನೇರ ಮಾಡಬೇಡಿ. ಹೇಗಿದೆಯೋ ಹಾಗೆಯೇ ಬಿಡಿ. ತೆರೆದ ಗಾಯವನ್ನು ಸ್ವಚ್ಛ ಬಟ್ಟೆಯಿಂದ ಮುಚ್ಚಿ.

### `OBJ1` · node E8
*When:* Object stuck in the body · *Sources:* IFAM, IFRC2020 · *Size:* en 77 B · hi 231 B · kn 237 B

- **en:** Do not pull out anything stuck in the body. Press cloth around it, not on it.
- **hi:** शरीर में घुसी किसी चीज़ को बाहर मत खींचिए। उसके चारों ओर कपड़ा रखकर दबाइए, उसके ऊपर नहीं।
- **kn:** ದೇಹದೊಳಗೆ ಚುಚ್ಚಿರುವ ವಸ್ತುವನ್ನು ಹೊರಗೆ ಎಳೆಯಬೇಡಿ. ಅದರ ಸುತ್ತ ಬಟ್ಟೆ ಇಟ್ಟು ಒತ್ತಿ, ಅದರ ಮೇಲೆ ಅಲ್ಲ.

### `SEIZ1` · node E9
*When:* Fitting or shaking reported · *Sources:* ERC2021, IFAM · *Size:* en 122 B · hi 276 B · kn 267 B

- **en:** Do not hold him down. Do not put anything in his mouth or hand. Move hard things away, and tell me when the shaking stops.
- **hi:** इन्हें पकड़कर मत दबाइए। मुँह या हाथ में कुछ मत डालिए। सख़्त चीज़ें दूर हटाइए, और झटके रुकें तो मुझे बताइए।
- **kn:** ಅವರನ್ನು ಹಿಡಿದು ಒತ್ತಬೇಡಿ. ಬಾಯಿಗೆ ಅಥವಾ ಕೈಗೆ ಏನೂ ಕೊಡಬೇಡಿ. ಗಟ್ಟಿ ವಸ್ತುಗಳನ್ನು ದೂರ ಸರಿಸಿ, ನಡುಕ ನಿಂತಾಗ ಹೇಳಿ.

### `BURN1` · node E10
*When:* Burn from exhaust or engine, and no higher-priority threat · *Sources:* ERC2021, IFRC2020 · *Size:* en 97 B · hi 233 B · kn 250 B

- **en:** Pour clean, cool water over the burn for twenty minutes. Do not put toothpaste, oil or ice on it.
- **hi:** जले हुए हिस्से पर बीस मिनट तक साफ़, ठंडा पानी डालिए। उस पर टूथपेस्ट, तेल या बर्फ़ मत लगाइए।
- **kn:** ಸುಟ್ಟ ಭಾಗದ ಮೇಲೆ ಇಪ್ಪತ್ತು ನಿಮಿಷ ಸ್ವಚ್ಛ, ತಣ್ಣೀರು ಸುರಿಯಿರಿ. ಟೂತ್‌ಪೇಸ್ಟ್, ಎಣ್ಣೆ ಅಥವಾ ಐಸ್ ಹಚ್ಚಬೇಡಿ.

### `MULTI1` · node E11
*When:* More than one person hurt · *Sources:* IFAM · *Size:* en 88 B · hi 189 B · kn 196 B

- **en:** How many people are hurt? Let's check each one, starting with anyone who is not talking.
- **hi:** कितने लोगों को चोट लगी है? हर एक को देखते हैं, पहले उन्हें जो बोल नहीं रहे।
- **kn:** ಎಷ್ಟು ಜನರಿಗೆ ಗಾಯವಾಗಿದೆ? ಪ್ರತಿಯೊಬ್ಬರನ್ನೂ ನೋಡೋಣ, ಮೊದಲು ಮಾತಾಡದೇ ಇರುವವರನ್ನು.

## Common unsafe requests

### `HELMET1` · node E-HELMET
*When:* Bystander wants to remove the helmet · *Sources:* IFAM, IFRC2020 · *Size:* en 91 B · hi 225 B · kn 277 B

- **en:** Please do not take off his helmet. It can hurt his neck. The ambulance team will remove it.
- **hi:** कृपया इनका हेलमेट मत उतारिए। इससे गर्दन को चोट लग सकती है। एम्बुलेंस टीम इसे उतारेगी।
- **kn:** ದಯವಿಟ್ಟು ಅವರ ಹೆಲ್ಮೆಟ್ ತೆಗೆಯಬೇಡಿ. ಅದರಿಂದ ಕುತ್ತಿಗೆಗೆ ಪೆಟ್ಟಾಗಬಹುದು. ಆಂಬ್ಯುಲೆನ್ಸ್ ತಂಡ ಅದನ್ನು ತೆಗೆಯುತ್ತದೆ.

### `WATER1` · node E-WATER
*When:* Bystander wants to give water, food, tea or medicine · *Sources:* IFAM · *Size:* en 76 B · hi 146 B · kn 164 B

- **en:** Please do not give him water, food or medicine yet. The doctors will decide.
- **hi:** अभी इन्हें पानी, खाना या दवा मत दीजिए। डॉक्टर तय करेंगे।
- **kn:** ಈಗ ಅವರಿಗೆ ನೀರು, ಊಟ ಅಥವಾ ಔಷಧಿ ಕೊಡಬೇಡಿ. ವೈದ್ಯರು ನಿರ್ಧರಿಸುತ್ತಾರೆ.

## Moving him

### `TRANS1` · node E-TRANSPORT
*When:* Bystander wants to take him in a private vehicle (default answer) · *Sources:* ERC2021, IFAM · *Size:* en 85 B · hi 233 B · kn 276 B

- **en:** Please wait for the ambulance. Moving him without support can hurt his neck and back.
- **hi:** कृपया एम्बुलेंस का इंतज़ार कीजिए। बिना सहारे के हिलाने से गर्दन और पीठ को चोट लग सकती है।
- **kn:** ದಯವಿಟ್ಟು ಆಂಬ್ಯುಲೆನ್ಸ್‌ಗಾಗಿ ಕಾಯಿರಿ. ಸರಿಯಾದ ಆಸರೆ ಇಲ್ಲದೆ ಸರಿಸಿದರೆ ಕುತ್ತಿಗೆ ಮತ್ತು ಬೆನ್ನಿಗೆ ಪೆಟ್ಟಾಗಬಹುದು.

### `TRANS2` · node E-TRANSPORT
*When:* ONLY after the 112 operator approves private transport · *Sources:* IFAM · **requires:** operator_approval · *Size:* en 127 B · hi 297 B · kn 319 B

- **en:** The ambulance team says to bring him. Use several people. Keep him lying flat, with his head, neck and body in a straight line.
- **hi:** एम्बुलेंस टीम ने इन्हें लाने को कहा है। कई लोग मिलकर उठाइए। इन्हें सीधा लिटाकर रखिए, सिर, गर्दन और शरीर एक सीध में।
- **kn:** ಅವರನ್ನು ಕರೆತರಲು ಆಂಬ್ಯುಲೆನ್ಸ್ ತಂಡ ಹೇಳಿದೆ. ಹಲವು ಜನ ಸೇರಿ ಎತ್ತಿ. ಅವರನ್ನು ನೇರವಾಗಿ ಮಲಗಿಸಿ, ತಲೆ, ಕುತ್ತಿಗೆ, ದೇಹ ಒಂದೇ ನೇರದಲ್ಲಿರಲಿ.

## Offline loop (pre-recorded Murf clips)

### `OFF1` · node B9
*When:* Offline loop (no data or agent unavailable), first clip · *Sources:* non-clinical · *Size:* en 96 B · hi 249 B · kn 253 B

- **en:** This rider has had an accident, and my internet is not working. Please call 112 from your phone.
- **hi:** इस राइडर का एक्सीडेंट हुआ है, और मेरा इंटरनेट काम नहीं कर रहा। कृपया अपने फ़ोन से 112 पर कॉल कीजिए।
- **kn:** ಈ ಸವಾರರಿಗೆ ಅಪಘಾತವಾಗಿದೆ, ನನ್ನ ಇಂಟರ್ನೆಟ್ ಕೆಲಸ ಮಾಡುತ್ತಿಲ್ಲ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಫೋನಿನಿಂದ 112 ಗೆ ಕರೆ ಮಾಡಿ.

### `OFF2` · node B9
*When:* Offline loop, only after the SMS was actually sent · *Sources:* non-clinical · *Size:* en 52 B · hi 166 B · kn 157 B

- **en:** I have sent his family a message with this location.
- **hi:** मैंने इनके परिवार को इस जगह की जानकारी के साथ मैसेज भेज दिया है।
- **kn:** ಈ ಸ್ಥಳದ ಮಾಹಿತಿಯೊಂದಿಗೆ ಅವರ ಕುಟುಂಬಕ್ಕೆ ಸಂದೇಶ ಕಳುಹಿಸಿದ್ದೇನೆ.

### `OFF3` · node B9
*When:* Offline loop (cannot ask questions, so it is conditional) · *Sources:* ERC2021, AHA2020 · *Size:* en 98 B · hi 220 B · kn 240 B

- **en:** If he is not breathing normally, push hard and fast on the centre of his chest until help arrives.
- **hi:** अगर ये ठीक से साँस नहीं ले रहे, तो मदद आने तक छाती के बीच में ज़ोर से और तेज़ी से दबाइए।
- **kn:** ಅವರು ಸರಿಯಾಗಿ ಉಸಿರಾಡುತ್ತಿಲ್ಲದಿದ್ದರೆ, ಸಹಾಯ ಬರುವವರೆಗೆ ಎದೆಯ ಮಧ್ಯದಲ್ಲಿ ಜೋರಾಗಿ, ವೇಗವಾಗಿ ಒತ್ತಿ.

### `OFF4` · node B9
*When:* Offline loop · *Sources:* ERC2021 · *Size:* en 82 B · hi 182 B · kn 204 B

- **en:** If he is bleeding heavily, press hard on the wound with a cloth and keep pressing.
- **hi:** अगर बहुत ख़ून बह रहा है, तो घाव पर कपड़े से ज़ोर से दबाइए और दबाते रहिए।
- **kn:** ತುಂಬಾ ರಕ್ತ ಹರಿಯುತ್ತಿದ್ದರೆ, ಗಾಯದ ಮೇಲೆ ಬಟ್ಟೆಯಿಂದ ಜೋರಾಗಿ ಒತ್ತಿ, ಒತ್ತುತ್ತಲೇ ಇರಿ.

## Offline loop order
Played on a loop from audio stored on the phone, each clip in the local language, then Hindi, then English: `OFF1` → `GS1` → `HELMET1` → `OFF3` → `OFF4` → `OFF2`. `OFF2` plays only if the SMS was actually sent.

## Sources
- **ERC2021:** European Resuscitation Council Guidelines 2021: First Aid (Zideman et al., Resuscitation 2021) and Basic Life Support
- **IFRC2020:** IFRC International First Aid, Resuscitation and Education Guidelines 2020
- **AHA2020:** 2020 American Heart Association Guidelines for CPR and ECC (hands-only CPR for untrained lay rescuers: rate 100-120/min, depth 5-6 cm)
- **IFAM:** Indian First Aid Manual (Indian Red Cross Society and St John Ambulance India)
- **GSR:** MoRTH Good Samaritan guidelines (2015), Section 134A Motor Vehicles Act (2019), Good Samaritan Rules (2020)
