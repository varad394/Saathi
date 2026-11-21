"""Settings loaded from the repo-root .env."""
import os
import pathlib

from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def _req(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise RuntimeError(f"Missing {name} in .env")
    return v


AGORA_APP_ID = _req("AGORA_APP_ID")
AGORA_APP_CERTIFICATE = _req("AGORA_APP_CERTIFICATE")
AGORA_CUSTOMER_ID = _req("AGORA_CUSTOMER_ID")
AGORA_CUSTOMER_SECRET = _req("AGORA_CUSTOMER_SECRET")

MURF_API_KEY = _req("MURF_API_KEY")
MURF_VOICE_ID = _req("MURF_VOICE_ID")
MURF_MODEL = os.getenv("MURF_MODEL", "falcon-2.1").strip()

# Family / 112 / hospital sessions use Murf's recommended (female) voice for that party's language.
# Source: Murf 'Recommended Indian voices' sheet linked in the hackathon FAQ. All verified in Murf's
# falcon-2.1 voice list to support the locale shown.
VOICE_BY_LANG = {
    "en": ("en-IN-pooja", "en-IN"), "hi": ("en-IN-pooja", "hi-IN"), "kn": ("en-IN-pooja", "kn-IN"),
    "ta": ("en-IN-pooja", "ta-IN"), "te": ("en-IN-pooja", "te-IN"),
    "mr": ("gu-IN-diya", "mr-IN"), "gu": ("gu-IN-diya", "gu-IN"), "ml": ("gu-IN-diya", "ml-IN"),
    "bn": ("bn-IN-debarati", "bn-IN"), "pa": ("pa-IN-harpreet", "pa-IN"),
    "as": ("en-IN-anisha", "as-IN"), "or": ("en-IN-anisha", "or-IN"),
}

SARVAM_API_KEY = _req("SARVAM_API_KEY")

LLM_BASE_URL = _req("LLM_BASE_URL").rstrip("/")
LLM_API_KEY = _req("LLM_API_KEY")
# Optional extra keys from OTHER Groq accounts (limits are per organisation; same-account keys share them)
LLM_API_KEYS = list(dict.fromkeys(  # LLM_API_KEY plus LLM_API_KEY_2 ... LLM_API_KEY_9, duplicates removed
    k for k in [LLM_API_KEY] + [os.getenv(f"LLM_API_KEY_{i}", "").strip() for i in range(2, 10)] if k))
LLM_MODEL = _req("LLM_MODEL")
LLM_FAST_MODEL = os.getenv("LLM_FAST_MODEL", "openai/gpt-oss-20b").strip()  # family/112/translation; own rate limit
SARVAM_LLM_MODEL = os.getenv("SARVAM_LLM_MODEL", "sarvam-105b").strip()      # last-resort fallback

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
CUSTOM_LLM_SHARED_KEY = _req("CUSTOM_LLM_SHARED_KEY")

# Fixed test identities (barebones: one channel, one phone, one agent)
CHANNEL = "saathi-test"
AGENT_UID = 999
USER_UID = 1001
