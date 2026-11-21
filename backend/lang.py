"""Per-utterance language detection (Agora does not forward Sarvam's detected language to our LLM)."""
import re

NAMES = {"en": "English", "hi": "Hindi", "kn": "Kannada", "mr": "Marathi", "ta": "Tamil", "te": "Telugu",
         "ml": "Malayalam", "bn": "Bengali", "gu": "Gujarati", "pa": "Punjabi", "or": "Odia", "as": "Assamese"}

# Unicode blocks with their own script
_BLOCKS = [("kn", 0x0C80, 0x0CFF), ("ta", 0x0B80, 0x0BFF), ("te", 0x0C00, 0x0C7F), ("ml", 0x0D00, 0x0D7F),
           ("bn", 0x0980, 0x09FF), ("gu", 0x0A80, 0x0AFF), ("pa", 0x0A00, 0x0A7F), ("or", 0x0B00, 0x0B7F),
           ("dev", 0x0900, 0x097F)]
_MR = {"आहे", "आहेत", "नाही", "काय", "मला", "तुम्ही", "झाले", "झाला", "आणि", "पण", "कुठे", "होता", "होते", "आहोत", "माझा", "माझी"}
_HI = {"है", "हैं", "नहीं", "क्या", "मुझे", "आप", "हुआ", "और", "लेकिन", "कहाँ", "था", "मेरा", "मेरी", "रहा", "रही"}
_HINGLISH = {"hai", "nahi", "nahin", "mera", "meri", "kya", "karo", "kar", "dard", "bhai", "haan", "accha", "theek", "ho", "raha"}


def detect(text: str) -> str | None:
    """Best-effort language code for one utterance, or None if unclear."""
    if not text or not text.strip():
        return None
    counts: dict[str, int] = {}
    for ch in text:
        cp = ord(ch)
        for code, lo, hi in _BLOCKS:
            if lo <= cp <= hi:
                counts[code] = counts.get(code, 0) + 1
                break
    if counts:
        code = max(counts, key=counts.get)
        if code != "dev":
            return code
        words = set(re.findall(r"[ऀ-ॿ]+", text))
        return "mr" if len(words & _MR) > len(words & _HI) else "hi"
    words = set(re.findall(r"[a-z]+", text.lower()))
    if not words:
        return None
    return "hi" if len(words & _HINGLISH) >= 2 else "en"


def word_count(text: str) -> int:
    return len(text.split())
