"""One-shot LLM helper: restate a NON-MEDICAL status message in another language.

Used for relays (family updates, confirmations, questions between sessions). Medical instructions never go
through here; those are fixed protocol lines spoken word for word.
"""
import logging
import time

import llmclient
from lang import NAMES

log = logging.getLogger("compose")

_SYS = ("You restate a short status message for a phone call. Output ONLY the message in {lang}, using its native script, "
        "in 1-3 short spoken sentences. Keep every fact exactly; add nothing; no medical advice; no phone numbers; "
        "never say the person is fine or that it is serious. Keep exactly who did what: never turn 'they' or 'he' into 'I'. "
        "You are Saathi, a female voice relaying information: use feminine first-person forms only for your own actions. "
        "Keep names, hospital names and numbers as they are. No emoji or symbols.")


async def to_lang(text_en: str, lang: str, audience: str = "") -> str:
    if lang == "en" or not text_en:
        return text_en
    t = time.perf_counter()
    try:
        out, _, prov = await llmclient.complete(
            [{"role": "system", "content": _SYS.format(lang=NAMES.get(lang, lang))},
             {"role": "user", "content": (f"Audience: {audience}\n" if audience else "") + text_en}], role="compose")
        out = out.replace("\u202f", " ").strip()
        log.info("compose %s via %s in %.0f ms: %r", lang, prov, (time.perf_counter() - t) * 1000, out[:120])
        return out or text_en
    except Exception:
        log.exception("compose failed; falling back to English")
        return text_en
