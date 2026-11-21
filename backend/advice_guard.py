"""Safety filter for LLM-generated first-aid advice (used only when no reviewed protocol line covers a question).

Blocks medicines and doses, injections, tourniquets, and instructions to remove the helmet / move / straighten /
pull / give food or drink, unless the sentence is a negation ("don't remove the helmet"). Blocked advice is
replaced by the reviewed holding line.
"""
import re

_NEG = re.compile(r"(don'?t|do not|never|avoid|\bno\b|\bnot\b|मत|नहीं|न करें|ಬೇಡ|ಮಾಡಬೇಡಿ|ತೆಗೆಯಬೇಡಿ)", re.I)
_ALWAYS = [r"\b\d+\s*(mg|ml|mcg|tablets?|pills?)\b", r"paracetamol|ibuprofen|aspirin|crocin|dolo|combiflam|disprin|diclofenac|morphine",
           r"inject|injection|इंजेक्शन|tourniquet", r"\bcpr\b.*\bbreaths?\b"]
_UNLESS_NEGATED = [r"(remove|take off|pull off).{0,15}helmet", r"हेलमेट.{0,10}(उतार|निकाल)", r"ಹೆಲ್ಮೆಟ್.{0,10}ತೆಗೆ",
                   r"\b(give|feed)\b.{0,15}\b(water|food|tea|juice|sugar|medicine|tablet|painkiller)",
                   r"(पानी|खाना|दवा|गोली).{0,12}(दे|दीजिए|दो)", r"(ನೀರು|ಊಟ|ಔಷಧ|ಮಾತ್ರೆ).{0,12}ಕೊಡಿ",
                   r"\b(straighten|pull|lift|sit him up|stand him up|move him)\b", r"\b(medicine|painkiller|tablet)\b"]


def check(advice: str) -> tuple[bool, str]:
    """Returns (ok, reason)."""
    text = (advice or "").strip()
    if not text:
        return False, "empty"
    if len(text) > 400:
        return False, "too long"
    for sent in re.split(r"(?<=[.!?।])\s+", text):
        s = sent.lower()
        for p in _ALWAYS:
            if re.search(p, s):
                return False, f"blocked: {p}"
        if not _NEG.search(s):
            for p in _UNLESS_NEGATED:
                if re.search(p, s):
                    return False, f"blocked: {p}"
    return True, "ok"
