"""Fast, deterministic rider-check intent: is this the rider saying he's fine? (en / hi / kn / mr)

Used before the LLM during RIDER_CHECK, so a clipped "Fine" or "theek hoon" cancels reliably and instantly.
Anything mentioning pain, help, blood or a negation is never treated as fine.
"""
import re

_OK = [r"\bfine\b", r"\bok(ay)?\b", r"\ball ?right\b", r"\bi'?m good\b", r"\bno problem\b", r"\bnothing happened\b",
       r"\b(theek|thik)\b", r"ठीक", r"बढ़िया", r"बरा आहे", r"ಚೆನ್ನಾಗಿದ್ದ", r"ಪರವಾಗಿಲ್ಲ", r"ಸರಿ ಇದ್ದ", r"ಆರಾಮ"]
_DANGER = [r"\bnot\b", r"\bno\b(?! problem)", r"n'?t\b", r"\bhelp", r"\bpain", r"\bhurt", r"\bblood", r"\bbleed",
           r"\bdard\b", r"\bmadad\b", r"\bnahi", r"दर्द", r"मदद", r"नहीं", r"नही", r"खून", r"ನೋವು", r"ಸಹಾಯ", r"ರಕ್ತ",
           r"ಆಗ್ತಿಲ್ಲ", r"ಇಲ್ಲ(?!ವ)(?<!ಪರವಾಗಿಲ್ಲ)", r"नाही", r"वेदना"]


def rider_says_fine(text: str) -> bool:
    t = (text or "").lower().strip()
    if not t or len(t.split()) > 8:  # long answers go to the LLM
        return False
    if any(re.search(p, t) for p in _DANGER):
        return False
    return any(re.search(p, t) for p in _OK)
