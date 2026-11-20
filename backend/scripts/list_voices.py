"""List Murf voices that cover en-IN, hi-IN and kn-IN. Usage: python backend/scripts/list_voices.py"""
import json
import os
import pathlib
import urllib.request

ENV = pathlib.Path(__file__).resolve().parents[2] / ".env"
for line in ENV.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.split("#", 1)[0].strip())

WANT = {"en-IN", "hi-IN", "kn-IN"}
req = urllib.request.Request(
    "https://api.murf.ai/v1/speech/voices?model=falcon-2.1",
    headers={"api-key": os.environ["MURF_API_KEY"], "Accept": "application/json"},
)
voices = json.load(urllib.request.urlopen(req, timeout=30))


def locales(v):
    locs = {v.get("locale", "")}
    sup = v.get("supportedLocales") or {}
    locs |= set(sup.keys() if isinstance(sup, dict) else sup)
    return locs


print(f"{len(voices)} voices total\n")
hits = [v for v in voices if WANT <= locales(v)]
print(f"Voices covering {sorted(WANT)}: {len(hits)}")
for v in hits:
    print(f"  {v.get('voiceId'):28} {v.get('displayName', ''):30} gender={v.get('gender', '')} base={v.get('locale')}")

print("\nIndian-base voices (any) for reference:")
for v in voices:
    if str(v.get("locale", "")).endswith("-IN"):
        extra = sorted(l for l in locales(v) if l.endswith("-IN"))
        print(f"  {v.get('voiceId'):28} {v.get('gender', ''):7} IN-locales={extra}")
