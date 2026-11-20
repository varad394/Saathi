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

SARVAM_API_KEY = _req("SARVAM_API_KEY")

LLM_BASE_URL = _req("LLM_BASE_URL").rstrip("/")
LLM_API_KEY = _req("LLM_API_KEY")
LLM_MODEL = _req("LLM_MODEL")

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
CUSTOM_LLM_SHARED_KEY = _req("CUSTOM_LLM_SHARED_KEY")

# Fixed test identities (barebones: one channel, one phone, one agent)
CHANNEL = "saathi-test"
AGENT_UID = 999
USER_UID = 1001
