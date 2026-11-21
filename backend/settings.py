"""Runtime settings, changeable from the dashboard or the phone app without a redeploy.

GET /settings returns them; POST /settings with a partial JSON object updates and saves them
(backend/data/settings.json, git-ignored). Timers apply immediately; ASR and voice-detection values apply to
the next incident (they are part of the agent's start request).
"""
import json
import pathlib

import config as C

_FILE = pathlib.Path(__file__).parent / "data" / "settings.json"

DEFAULTS = {
    # speech recognition
    "asr_vendor": C.ASR_VENDOR,            # "sarvam" (auto language) | "ares" (Agora built-in)
    "ares_langs": C.ARES_SCENE_LANGS,      # languages ARES listens for in the scene, comma-separated
    # Agora voice activity detection (turn_detection.config)
    "speech_threshold": 0.75,               # 0..1; higher ignores quieter / distant voices (background chatter)
    "silence_ms": 900,                     # silence that ends a turn (longer = fewer split sentences)
    # phone / dashboard microphone processing (applied by the client when it opens the mic)
    "mic_aec": False,                      # echo cancellation: on for loudspeaker, off for headsets
    "mic_ans": True,                       # noise suppression: keep on in noisy places
    "mic_agc": True,                       # automatic gain
    "ains_mode": 1,                        # phone AI noise suppression: 0 balanced, 1 aggressive, 2 aggressive + low latency
    "playback_gain": 300,                  # phone loudspeaker boost for Saathi's voice, 0-400 (100 = normal); roads are loud
    "mic_gain": 100,                       # phone mic level, 0-400 (100 = normal)
    # workflow timers (seconds)
    "rider_check_s": 20,
    "greeting_s": 9,
    "cancel_undo_s": 10,
    "listen_after_cancel_s": 60,
    "rider_silent_s": 15,
    "announce_every_s": 35,
}
LIMITS = {"playback_gain": (0, 400), "mic_gain": (0, 400), "ains_mode": (0, 2), "speech_threshold": (0.1, 0.95), "silence_ms": (300, 2000), "rider_check_s": (5, 120), "greeting_s": (0, 30),
          "cancel_undo_s": (3, 60), "listen_after_cancel_s": (5, 600), "rider_silent_s": (5, 120), "announce_every_s": (10, 300)}

_cur = dict(DEFAULTS)


def _load() -> None:
    if _FILE.exists():
        try:
            saved = json.loads(_FILE.read_text(encoding="utf-8"))
            _cur.update({k: v for k, v in saved.items() if k in DEFAULTS})
        except Exception:
            pass


def get(key: str):
    return _cur[key]


def all_() -> dict:
    return dict(_cur)


def update(patch: dict) -> dict:
    for k, v in patch.items():
        if k not in DEFAULTS:
            continue
        typ = type(DEFAULTS[k])
        v = (str(v).lower() in ("1", "true", "yes", "on")) if typ is bool else typ(v)
        if k in LIMITS:
            lo, hi = LIMITS[k]
            v = max(lo, min(hi, v))
        if k == "asr_vendor" and v not in ("sarvam", "ares"):
            continue
        _cur[k] = v
    _FILE.parent.mkdir(exist_ok=True)
    _FILE.write_text(json.dumps(_cur, indent=2), encoding="utf-8")
    return all_()


def reset() -> dict:
    _cur.clear()
    _cur.update(DEFAULTS)
    if _FILE.exists():
        _FILE.unlink()
    return all_()


_load()
