"""Fast-path shortcuts for the two most time-critical rider answers. Deliberately NARROW: only short, unambiguous,
first-person or bare phrases ("I'm fine", "ok", "help", "मदद"). Anything longer, negated, or about someone else
("he is fine", "don't call for help") goes to the LLM, which understands context, negation and who is speaking.
"""
import re

MAX_WORDS = 4
_THIRD = [r"\b(he|she|him|his|her|they|them)\b", r"\b(wo|woh|vo|uska|usko|unka|unko)\b", r"वो", r"वह", r"उस", r"उन",
          r"ಅವನು", r"ಅವಳು", r"ಅವರು", r"ಅವನಿಗೆ", r"ಅವರಿಗೆ", r"तो\b", r"त्याला", r"ती\b"]
_NEG = [r"\bnot?\b", r"n'?t\b", r"\bnever\b", r"\bmat\b", r"\bnahi", r"मत", r"नहीं", r"नही", r"ಬೇಡ", r"ಇಲ್ಲ", r"नको", r"नाही"]
_OK = [r"\bfine\b", r"\bok(ay)?\b", r"\ball ?right\b", r"\bi'?m good\b", r"\b(theek|thik)\b", r"ठीक", r"बरा",
       r"ಚೆನ್ನಾಗಿದ್ದ", r"ಪರವಾಗಿಲ್ಲ", r"ಆರಾಮ"]
_HELP = [r"\bhelp\b", r"\bbachao\b", r"\bmadad\b", r"मदद", r"बचाओ", r"ಸಹಾಯ", r"ಕಾಪಾಡಿ", r"मदत"]


def _short(t: str) -> bool:
    return 0 < len(t.split()) <= MAX_WORDS


def _any(pats, t) -> bool:
    return any(re.search(p, t) for p in pats)


def rider_says_fine(text: str) -> bool:
    t = (text or "").lower().strip(" .!?")
    if not _short(t) or _any(_THIRD, t) or _any(_HELP, t):
        return False
    if _any(_NEG, t) and not re.search(r"ಪರವಾಗಿಲ್ಲ", t):  # "ಪರವಾಗಿಲ್ಲ" (no problem) contains a negation but means fine
        return False
    return _any(_OK, t)


def rider_needs_help(text: str) -> bool:
    t = (text or "").lower().strip(" .!?")
    return _short(t) and _any(_HELP, t) and not _any(_NEG, t) and not _any(_THIRD, t)
