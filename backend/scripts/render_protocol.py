"""Validate backend/protocol/first_aid.json and render docs/first_aid_protocol.md from it.

The JSON is the single source of truth: the backend speaks these lines word for word,
and reviewers read the rendered Markdown. Run after every edit:
    python backend/scripts/render_protocol.py
Exits non-zero if any line breaks a rule (missing language, over Agora's 512-byte speak limit, bad source key).
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "protocol" / "first_aid.json"
OUT = ROOT / "docs" / "first_aid_protocol.md"
LANGS = [("en", "English (source text; also the meaning of the other columns)"), ("hi", "Hindi"), ("kn", "Kannada")]
SPEAK_LIMIT = 512
GROUPS = [
    ("scene", "Scene lines"), ("safety", "Scene safety"), ("assess", "Assessment"), ("cpr", "Not breathing: hands-only CPR"),
    ("bleeding", "Bleeding"), ("unconscious", "Unconscious but breathing"), ("conscious", "Conscious rider"),
    ("injuries", "Other injuries"), ("donts", "Common unsafe requests"), ("transport", "Moving him"),
    ("offline", "Offline loop (pre-recorded Murf clips)"),
]

data = json.loads(SRC.read_text(encoding="utf-8"))
errors, worst = [], 0
ids = set()
for ln in data["lines"]:
    if ln["id"] in ids:
        errors.append(f"duplicate id {ln['id']}")
    ids.add(ln["id"])
    for code, _ in LANGS:
        text = ln.get(code, "").strip()
        if not text:
            errors.append(f"{ln['id']}: missing {code}")
            continue
        n = len(text.encode("utf-8"))
        worst = max(worst, n)
        if n > SPEAK_LIMIT:
            errors.append(f"{ln['id']}.{code}: {n} bytes > {SPEAK_LIMIT}")
    for s in ln.get("src", []):
        if s not in data["sources"]:
            errors.append(f"{ln['id']}: unknown source {s}")
for i in data.get("offline_loop", []):
    if i not in ids:
        errors.append(f"offline_loop: unknown id {i}")

out = [
    "# Saathi first-aid protocol (spoken word for word)",
    "",
    f"**Version {data['version']}.** Generated from `backend/protocol/first_aid.json` by "
    "`backend/scripts/render_protocol.py`. Edit the JSON, not this file.",
    "",
    "> **Review status**",
    *[f"> - **{k.replace('_', ' ')}:** {v}" for k, v in data["status"].items()],
    "",
    "Every line below is spoken through Agora's `speak` API exactly as written. The LLM only chooses *which* line "
    "(by ID); it never writes medical text. The English line is the source, and the Hindi and Kannada lines say "
    "the same thing. Node IDs (E0, E4a, …) refer to the tree in [scenario_tree.md](scenario_tree.md).",
    "",
    "## Principles",
    *[f"{i}. {p}" for i, p in enumerate(data["principles"], 1)],
    "",
    "## What Saathi deliberately does not say",
    "| Not said | Why |",
    "|---|---|",
    *[f"| {x['what']} | {x['why']} |" for x in data["excluded"]],
    "",
]
for gid, title in GROUPS:
    lines = [ln for ln in data["lines"] if ln["group"] == gid]
    if not lines:
        continue
    out += [f"## {title}", ""]
    for ln in lines:
        sizes = " · ".join(f"{c} {len(ln[c].encode('utf-8'))} B" for c, _ in LANGS)
        src = ", ".join(ln.get("src", [])) or "non-clinical"
        req = f" · **requires:** {ln['requires']}" if ln.get("requires") else ""
        out += [
            f"### `{ln['id']}` · node {ln['node']}",
            f"*When:* {ln['when']} · *Sources:* {src}{req} · *Size:* {sizes}",
            "",
            *[f"- **{code}:** {ln[code]}" for code, _ in LANGS],
            "",
        ]
out += [
    "## Offline loop order",
    "Played on a loop from audio stored on the phone, each clip in the local language, then Hindi, then English: "
    + " → ".join(f"`{i}`" for i in data["offline_loop"]) + ". `OFF2` plays only if the SMS was actually sent.",
    "",
    "## Sources",
    *[f"- **{k}:** {v}" for k, v in data["sources"].items()],
    "",
]
OUT.write_text("\n".join(out), encoding="utf-8")
print(f"{len(data['lines'])} lines x {len(LANGS)} languages; largest {worst} bytes (limit {SPEAK_LIMIT})")
if errors:
    print("ERRORS:\n  " + "\n  ".join(errors))
    sys.exit(1)
print(f"wrote {OUT.relative_to(ROOT)}")
