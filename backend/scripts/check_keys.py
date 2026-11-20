"""Live-check every key in .env without printing secrets. Usage: python backend/scripts/check_keys.py"""
import base64
import json
import os
import pathlib
import time
import urllib.error
import urllib.request

ENV = pathlib.Path(__file__).resolve().parents[2] / ".env"
for line in ENV.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.split("#", 1)[0].strip())
E = os.environ


def call(url, headers=None, body=None, method=None):
    data = json.dumps(body).encode() if body is not None else None
    h = {"Accept": "application/json", "User-Agent": "saathi-dev", **(headers or {})}
    if data:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    t = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode(), time.perf_counter() - t
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300], time.perf_counter() - t


def show(name, ok, detail):
    print(f"[{'OK ' if ok else 'FAIL'}] {name}: {detail}")


# 1. Groq: models list
s, b, _ = call(f"{E['LLM_BASE_URL']}/models", {"Authorization": f"Bearer {E['LLM_API_KEY']}"})
if s == 200:
    ids = sorted(m["id"] for m in json.loads(b)["data"])
    show("LLM key", True, f"{len(ids)} models; configured model present: {E['LLM_MODEL'] in ids}")
    print("       chat-ish models:", [i for i in ids if any(x in i for x in ("llama", "gpt-oss", "qwen", "kimi", "gemma"))])
else:
    show("LLM key", False, f"{s} {b}")

# 2. Groq: tool call + latency (non-streaming, rough)
tools = [{"type": "function", "function": {
    "name": "log_rider_status", "description": "Record the rider's condition and their words.",
    "parameters": {"type": "object", "properties": {
        "status": {"type": "string", "enum": ["ok", "injured", "no_response"]},
        "words": {"type": "string"}}, "required": ["status", "words"]}}}]
body = {"model": E["LLM_MODEL"], "tools": tools, "tool_choice": "auto", "max_tokens": 300, "reasoning_effort": "low", "messages": [
    {"role": "system", "content": "You are Saathi, a crash responder. Always call log_rider_status for what the rider says."},
    {"role": "user", "content": "mera pair mein bahut dard hai, help karo"}]}
s, b, dt = call(f"{E['LLM_BASE_URL']}/chat/completions", {"Authorization": f"Bearer {E['LLM_API_KEY']}"}, body)
if s == 200:
    msg = json.loads(b)["choices"][0]["message"]
    tc = msg.get("tool_calls") or []
    show("LLM tool call", bool(tc), f"{dt*1000:.0f} ms total; " + (f"{tc[0]['function']['name']}({tc[0]['function']['arguments']})" if tc else f"no tool call, said: {msg.get('content')!r}"))
else:
    show("LLM tool call", False, f"{s} {b}")

# 3. Agora REST Basic auth (list agents in project)
cred = base64.b64encode(f"{E['AGORA_CUSTOMER_ID']}:{E['AGORA_CUSTOMER_SECRET']}".encode()).decode()
s, b, _ = call(f"https://api.agora.io/api/conversational-ai-agent/v2/projects/{E['AGORA_APP_ID']}/agents",
               {"Authorization": f"Basic {cred}"})
show("Agora REST auth", s == 200, f"{s} {b[:200]}")

# 4. Murf voices (already verified once)
s, b, _ = call("https://api.murf.ai/v1/speech/voices?model=falcon-2.1", {"api-key": E["MURF_API_KEY"]})
ok = s == 200 and any(v.get("voiceId") == E["MURF_VOICE_ID"] for v in json.loads(b))
show("Murf key + voice", ok, f"{s}; voice {E['MURF_VOICE_ID']} found: {ok}")

# 5. Sarvam key (tiny chat call - only validates the key; ASR itself is tested via Agora later)
s, b, dt = call("https://api.sarvam.ai/v2/chat/completions",
                {"Authorization": f"Bearer {E['SARVAM_API_KEY']}", "api-subscription-key": E["SARVAM_API_KEY"]},
                {"model": "sarvam-105b", "max_tokens": 20, "messages": [{"role": "user", "content": "Say hi in Kannada."}]})
show("Sarvam key", s == 200, f"{s} {dt*1000:.0f} ms " + ((json.loads(b)["choices"][0]["message"].get("content") or "(empty content)")[:60] if s == 200 else b[:200]))
