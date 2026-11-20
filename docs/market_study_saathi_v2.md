# Market Study: Saathi, Voice Crash Responder for Two-Wheeler Riders

**Version:** 2 (21 November 2026)
**Target market:** Office commuters on two-wheelers in India's big metros. Bengaluru is the first city.

**How to read the sources.** Every number has a source next to it. A number marked **[verify]** came from the first draft and still needs a link before it goes on a slide. If you can't find a link, drop it. Two or three linked numbers are worth more than fifteen unlinked ones.

---

## Executive summary

- **The problem is big.** In 2023, two-wheeler riders were **44.8%** of road deaths in India: **77,539 people** (MoRTH, *Road Accidents in India 2023*).
- **It's worse in our first city.** Bengaluru had **915** road deaths in 2023, the second-highest of any Indian city after Delhi. Two-wheelers accounted for **55%** of them (NCRB, *Accidental Deaths & Suicides in India 2023*).
- **Most riders' phones can't help on their own.** Automatic crash detection exists only on Google Pixel and recent iPhones, which are a small share of phones in India **[verify: add a market share source]**. Connected electric scooters cover even fewer riders: EVs were only about **6.5%** of new two-wheeler sales in FY26 (FADA, via Autocar Pro).
- **Existing tools send alerts. Nothing manages the scene.** No current tool talks to the bystanders around the rider, works across languages, or briefs the family and the hospital.
- **Saathi covers the first 10 minutes of the golden hour.** The golden hour is the first 60 minutes after a crash. Saathi handles the first 10, from detection until help is on the way, and stays useful through the handover to the hospital.

---

## 0. Phones: what riders already have

| | Budget and mid-range Android | Google Pixel | iPhone 14 and newer | Saathi |
| --- | --- | --- | --- | --- |
| Automatic crash detection | Generally none **[verify per brand]** | Yes, designed for car crashes | Yes, designed for car crashes | Yes, tuned for two-wheeler falls |
| How an alert starts | The user presses the power button several times (the count varies by brand) | Detected automatically | Detected automatically | Detected automatically |
| What happens next | Calls 112 and/or sends location to contacts | Calls emergency services with an automated message | Calls emergency services and notifies contacts | Checks the rider, talks to bystanders, calls family and 112 |
| Talks to bystanders in Indian languages | No | No **[verify Indian language support]** | No | Yes |
| Lock-screen medical info | Hidden in brand-specific menus | Shown on the lock screen if set up | Medical ID, if the user enabled it | Spoken aloud when a responder asks |

**Takeaways for the pitch**
1. **The lock-screen gap.** Built-in SOS on most Android phones assumes the rider is conscious and can press a button. If he's unconscious, the phone stays silent.
2. **Automatic detection is limited to a few phone models.** Use a sourced market share figure here (for example from IDC or Counterpoint). The first draft's brand-by-brand split had no source, so it's removed.

---

## 1. Which cities

We're targeting metros where many people ride to work and mobile data is reliable.

**Road deaths in 2023 in cities with over a million people (MoRTH, Section 6)**

| City | Road deaths, 2023 | Source |
| --- | --- | --- |
| Delhi | 1,457 | MoRTH 2023 (reported by Deccan Chronicle) |
| Bengaluru | 915 | MoRTH 2023 (reported by Deccan Chronicle) |
| Jaipur | 849 | MoRTH 2023 (reported by Deccan Chronicle) |
| Pune | [fill from MoRTH Table 6.2] | |
| Hyderabad | [fill from MoRTH Table 6.2] | |
| Chennai | [fill from MoRTH Table 6.2] | |
| Mumbai | [fill from MoRTH Table 6.2] | |

- Across cities with over a million people, two-wheelers were involved in **48.6%** of road accidents in 2023 (MoRTH 2023, reported by News Karnataka).
- **Mumbai:** check how much of its commuting is by two-wheeler before including it. Most Mumbai commuters use local trains, buses and autos.
- **Why Bengaluru first:** it has the second-highest road deaths of any city, the best local data, and it's where our team and the judges are.

**Be honest about scope.** Most road deaths in India happen outside cities: rural areas account for **69%** (IndiaSpend's analysis of MoRTH data). Cities are where Saathi starts, because that's where the phone, mobile data and an ambulance can all be counted on. They are not where most deaths happen.

---

## 2. Market size (Bengaluru first)

No agency counts "two-wheeler office commuters" directly. We estimate from three sources:

1. **Registered two-wheelers:** **86.04 lakh** non-transport two-wheelers in Bengaluru as of 31 March 2026, about **68.3%** of all registered vehicles in the city (Karnataka Transport Department) **[verify: add link]**. *The first draft also said 86.3% in one place. That was a typo.*
2. **Share of daily trips made by two-wheeler:** **27.1%** of daily trips in Bengaluru (Bengaluru Comprehensive Mobility Plan, BMRCL/DULT) **[verify: add link]**.
3. **The Outer Ring Road tech corridor:** about **10 lakh** people work in **26** tech parks along it (Outer Ring Road Companies Association) **[verify: add link]**.

**Sizing line for the pitch:**
> "Bengaluru alone has 86 lakh registered two-wheelers. About 1 in 4 daily trips in the city is made on one, and about 10 lakh people work in the tech parks along the Outer Ring Road. That's where we start, and other metros follow."

**Other metros:** [registered two-wheelers per city, from the Vahan dashboard or each state's transport department].

---

## 3. Crashes: India vs Bengaluru

| Measure | Value | Source |
| --- | --- | --- |
| Road deaths in India, 2023 | 1,72,890 | MoRTH 2023 |
| Two-wheeler riders' share of deaths, India, 2023 | 44.8% (77,539 people) | MoRTH 2023 |
| Road deaths in Bengaluru, 2023 | 915 (about 2.5 a day) | MoRTH 2023 / NCRB 2023 |
| Two-wheelers' share of Bengaluru deaths, 2023 | 55% | NCRB 2023 (reported by Deccan Herald) |
| Road deaths in Bengaluru, 2024 | 894 (from 4,769 accidents) | MoRTH 2024 (reported by Deccan Herald) |
| Accidents in Bengaluru, 2025 | 5,459 | Bengaluru Traffic Police **[verify]** |

**About the two Bengaluru shares.** A Bengaluru Traffic Police report (with Bloomberg Philanthropies' road safety programme) gives a different figure: 59% (542 of 909 deaths) **[verify: add link]**. Pitch the 55% NCRB figure, because it's linked and lower. Don't mix the two.

**Crashes with no other vehicle involved.** Skids, potholes and losing control on flyovers late at night. These are where Saathi helps most, because no other driver is there to stop and call for help. *The first draft's "3.34% increase" figure is removed: it had no source, and a 3% rise isn't a strong point anyway.*

---

## 4. The biggest risk: where commuters keep their phone

Saathi depends on the phone staying with the rider after a fall, in a pocket or bag. **This hasn't been tested yet.** Many commuters may use a handlebar mount for Google Maps.

**Quick survey (10–15 commuters, run at the venue)**
1. On your daily commute, where is your phone? Front pocket / jacket pocket / backpack / handlebar mount / scooter storage
2. Do you use a handlebar mount on your usual route? Every day / only for new routes / never
3. Do you ride with Bluetooth earbuds or a helmet intercom? Yes / No

**What to do with the results**
- **If fewer than 25% use a mount:** keep the current claim that the phone stays with the rider.
- **If 25% or more use a mount:**
    1. **Loudspeaker still works.** A phone thrown from a mount ends up on the road where bystanders gather, so the loudspeaker announcement still reaches them.
    2. **Bluetooth fallback (future).** Listen through the rider's Bluetooth earbuds or helmet headset during the first 20-second check, so Saathi hears him even if the phone is metres away.

---

## 5. The language gap

In metros, the people at a crash site often don't speak the same language as the rider's family.

**Bengaluru (Census 2011)**
- Kannada is the mother tongue of about **44%** of residents **[verify against the Census 2011 language table]**.
- Tamil, Telugu and Urdu are each about 12–14%, and Hindi about 5% **[verify the same table]**. *The first draft's Malayalam figure of 6% may be too high. Check it.*
- About **44%** of Bengaluru Urban's population were migrants, more than **16 lakh** of them from other states **[verify: Census 2011 migration tables]**.

**Other metros:** the same pattern holds. Bystanders speak Marathi in Pune, Telugu in Hyderabad and Tamil in Chennai, while families who moved from other states may speak something else **[add migration data per city]**.

*Removed from the first draft because they had no source: "Hindi 25%+ in tech corridors" (the census doesn't break down to that level) and "Kannada share is second-lowest among state capitals after Hyderabad."*

**Pitch line:** A commuter from Maharashtra or West Bengal crashes on the Outer Ring Road. The person who helps him speaks Kannada or Tamil, and his parents speak Marathi or Bengali. Saathi talks to each of them in their own language.

---

## 6. Why bystanders don't help

SaveLIFE Foundation's research shows that fear of legal trouble, not indifference, is the main reason **[verify: add the study name, year and link]**:
- **74%** of people said they were unlikely to help an injured crash victim.
- Of those, **88%** cited fear of legal hassles and police questioning, and **77%** cited fear of being held at the hospital or made to pay.
- More than **84%** of people didn't know about Good Samaritan protections (later SaveLIFE survey) **[verify]**.

*Removed: "88% willing to help if legally protected." It had no source, and the same 88% already appears above for a different finding.*

**Legal basis.** The Supreme Court's 2016 Good Samaritan guidelines (*SaveLIFE Foundation v. Union of India*), made law through Section 134A of the Motor Vehicles Act in 2019.

**Corrected script line.** The first draft's line, "You will not face police questioning or hospital bills," promised more than the law does. Use:
> "You're protected by law. You don't have to give your name, be a witness, or pay the hospital."

Check this wording against the official guidelines before the demo. This is not legal advice.

---

## 7. Delays in getting care and finding the family

- **Unidentified patients at NIMHANS, Bengaluru.** A study of trauma patients admitted without identity is relevant here. The first draft listed specific percentages (unconscious on arrival, unstable vital signs, transfers from other hospitals, deaths before family were found) **[verify each figure and add the citation before using any of them]**.
- **Preventable deaths.** The claims that "about 50% of road deaths are preventable with timely care" (often attributed to the Law Commission) and "over 30% are due to delays" (attributed to NITI Aayog) both need their original reports **[verify]**.

*Removed: "social workers take 4 to 18 hours to trace relatives" and "over 50% need immediate surgery." Neither had a source.*

---

## 8. Competitors

| Category | Examples | What they do | Where Saathi is different |
| --- | --- | --- | --- |
| Connected scooters and bikes | Ather, TVS (SmartXonnect), Ola | Some send fall or crash alerts to contacts through the brand's app **[verify which models]** | Works on any two-wheeler; talks to the people at the scene |
| Flagship phone features | iPhone Crash Detection, Pixel Car Crash Detection | Detect car crashes, call emergency services with an automated message | Tuned for two-wheelers, works on budget Android, speaks Indian languages |
| Budget Android SOS | Built into Android phones from Samsung, Xiaomi, Vivo, Oppo and others | Manual: press the power button several times; sends location | Automatic detection, hands-free voice |
| Smart helmets | Various Indian brands **[verify names and features]** | Impact sensors that send app alerts | Nothing new to buy; guides the people at the scene |
| Government app | 112 India | Manual panic button; sends location to the state control room | Automatic detection, coordinates several people |

**What sets Saathi apart**
1. **It works on the bikes and phones people already own.** EVs were only about 6.5% of new two-wheeler sales in FY26, so about 93% of new two-wheelers are petrol, and an even larger share of bikes already on the road. *The first draft's "16% EV share" was wrong. That figure is Ather's share within the EV segment.* One caveat: TVS SmartXonnect is also offered on some petrol models. Check which models have crash alerts before saying "petrol riders have nothing."
2. **It manages the scene, not just an alert.** Competitors send a location pin. Saathi talks to bystanders in their language, guides first aid from a fixed script, and briefs the family and the paramedic.

---

## 9. Who pays

Individual riders rarely pay for safety apps. Saathi is free for riders, paid for by organisations.

1. **Employers (first to test).** Companies already pay for commute safety for cab users, such as trip tracking and safe drops for women employees. Saathi gives the same kind of protection to employees who ride. Price per employee per month.
2. **Insurers.** Two-wheeler owners must have personal accident cover of ₹15 lakh for the owner-driver **[verify current rules]**. Insurers could bundle Saathi with policies, on the bet that faster help means less severe claims. *The first draft's "$6.5 billion" market size is removed until it has a source.*

> **Limit to state openly:** Nobody has tested yet whether employers or insurers will pay. After the hackathon, the next step is pilots with employers' HR and safety teams in metros, and talks with motor insurers.

---

## 10. Rules and regulations

### Data protection (DPDP Act, 2023)
- **Consent at setup.** The rider agrees to storing medical details (blood group, allergies, emergency contacts) on the phone.
- **Medical emergency exception.** Section 7(f) of the DPDP Act allows personal data to be processed without fresh consent to respond to a medical emergency that threatens someone's life or health **[verify the exact wording against the Act]**.
- **Privacy by design.** Medical data stays on the phone. It's only shared or read out after a crash is detected, and family numbers are never read out to strangers.

### Emergency numbers: just call 112
- On **26 May 2026**, the Supreme Court (*SaveLIFE Foundation v. Union of India*, 2026 INSC 567) held that trauma care is part of the right to life. It **ordered** all states and union territories to fully merge their emergency and ambulance helplines, including 108, into **112** within three months.
- *Correction to the first draft:* the ruling ordered this merger. It didn't confirm that Karnataka has finished it. Check Karnataka's current status before claiming it in the pitch.
- **For the product:** Saathi calls **112** by default. The first draft's private hospital hotline option (Apollo, Manipal and similar) is moved to future scope.

---

## 11. Before the pitch

1. **Run the phone survey** (section 4). It's the biggest open risk.
2. **Fill in the metro table** (section 1) from MoRTH 2023 Table 6.2.
3. **Find links for the [verify] items you plan to use, and drop the rest.**
4. **Check connected-scooter crash alerts** (TVS, Ather), including on petrol models.
5. **Check the Good Samaritan script line** against the official guidelines.

---

## Sources found during review

- MoRTH 2023 two-wheeler share (44.8%) and total deaths: [The Print](https://theprint.in/india/20-lives-lost-in-road-accidents-every-hour-in-2023-half-the-victims-bike-riders-delhi-deadliest-city/2358802), [Siasat](https://www.siasat.com/1-72-lakh-people-died-in-road-accidents-in-2023-road-ministry-report-3264450/)
- 77,539 two-wheeler deaths in 2023: [Daily Excelsior (PTI)](https://www.dailyexcelsior.com/?p=2140200)
- MoRTH report itself: [Road Accidents in India 2023 (PDF)](https://morth.nic.in/sites/default/files/Road-Accident-in-India-2023-Publications.pdf)
- Bengaluru 915 deaths, 55% two-wheelers (NCRB 2023): [Deccan Herald](https://www.deccanherald.com/amp/story/india%2Fkarnataka%2Fbengaluru%2Fbengaluru-tops-country-in-pedestrian-deaths-for-second-year-3750982)
- Bengaluru 2024 (894 deaths, 4,769 accidents): [Deccan Herald](https://www.deccanherald.com/india/karnataka/bengaluru/bengaluru-records-second-highest-pedestrian-deaths-among-million-plus-cities-in-2024-4071330)
- City deaths 2023 (Delhi, Bengaluru, Jaipur): [Deccan Chronicle](https://www.deccanchronicle.com/southern-states/telangana/risky-highways-drive-telangana-crash-toll-1928999)
- Two-wheelers 48.6% of accidents in cities with over a million people: [News Karnataka](https://newskarnataka.com/india/delhi-remains-hotspot-million-plus-cities-account-for-disproportionate-road-deaths/29082025/)
- Bengaluru Traffic Police and Bloomberg Philanthropies road safety report 2023: [OpenCity (PDF)](https://data.opencity.in/dataset/7b6fab44-c380-4359-a8a9-01c8787acd57/resource/6c425f17-b19b-402f-a638-6b9cae856025/download/bigrs_2023_btp_roadsafetyreport_final_compressed.pdf)
- Rural share of deaths (69%): [Newslaundry / IndiaSpend](https://www.newslaundry.com/2025/11/10/more-two-wheelers-gig-workers-under-pressure-in-india-9-bike-riders-die-every-hour)
- EV share of two-wheeler sales, FY26 (about 6.5%): [Autocar Pro](https://www.autocarpro.in/news/india-e2w-registrations-rise-22-to-14-million-units-in-fy26-penetration-at-65-131923)
- Supreme Court ruling, 26 May 2026: [Supreme Court order (PDF)](https://api.sci.gov.in/supremecourt/2024/49959/49959_2024_3_60_71558_FinalOrder_26-May-2026.pdf), [LiveLaw](https://www.livelaw.in/top-stories/trauma-care-part-of-right-to-life-supreme-court-directs-to-integrate-emergency-helplines-into-112-implement-pm-rahat-good-samaritan-scheme-536001)

---

## What changed from the first draft

| Section | Change |
| --- | --- |
| Scope | Changed from Bengaluru only to metros, with Bengaluru as the first city; added a city table |
| Executive summary | "First 10 minutes" is now described as part of the golden hour, not the golden hour itself |
| Executive summary, 3 | Bengaluru's two-wheeler share is now 55% (NCRB, linked); the 59% figure is kept as an alternate |
| 0 | Removed the unsourced brand market share split and the ₹55,000 price claim |
| 2 | Fixed the 86.3% / 68.3% contradiction |
| 3 | Removed the 3.34% self-accident figure; added Bengaluru 2024 data and the rural caveat |
| 5 | Removed the tech-corridor Hindi and state-capital ranking claims |
| 6 | Removed "88% willing if protected"; corrected the script line |
| 7 | Removed the "4 to 18 hours" and "over 50% need surgery" claims |
| 8 | EV share corrected from 16% to about 6.5%; added the TVS petrol caveat |
| 9 | Removed the $6.5B insurance figure |
| 10 | Supreme Court ruling described accurately; 112 is now the default; private hotlines moved to future scope |
