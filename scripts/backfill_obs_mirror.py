#!/usr/bin/env python3
"""One-off: mirror existing OBS bank documents to .decisions/obs/.

Bank is source of truth for content; the mirror is a browse derivative and
carries the lifecycle Status line (bank is append-only). Safe to re-run:
skips existing files.
"""
import json
import pathlib
import re
import urllib.request

DAEMON = "http://localhost:9077"
ROOT = pathlib.Path(__file__).resolve().parent.parent
OBS_DIR = ROOT / ".decisions" / "obs"
BANNER = ("<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this "
          "file is a browse mirror in the Hindsight repo. Observed evidence, "
          "not a held philosophy. -->\n\n**Status:** active\n\n")


def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def slug_from(text, doc_id):
    first = next((l for l in text.splitlines() if l.strip()), doc_id)
    first = re.sub(r"^#+\s*", "", first)
    first = re.sub(rf"^{doc_id}\s*[—-]\s*", "", first).strip()
    s = re.sub(r"[^a-z0-9]+", "-", first.lower()).strip("-")
    return s[:60] or "untitled"


def main():
    OBS_DIR.mkdir(parents=True, exist_ok=True)
    docs = get(f"{DAEMON}/v1/default/banks/oracle/documents")
    items = docs if isinstance(docs, list) else docs.get("items") or docs.get("result") or []
    total = docs.get("total") if isinstance(docs, dict) else len(items)
    if total and total > len(items):
        raise SystemExit(f"pagination needed: total={total} > page={len(items)}; "
                         "add a paging loop before re-running")
    obs_ids = sorted(d["id"] for d in items if str(d.get("id", "")).startswith("OBS-"))
    for doc_id in obs_ids:
        d = get(f"{DAEMON}/v1/default/banks/oracle/documents/{doc_id}")
        text = d.get("original_text") or d.get("text") or ""
        if not text:
            print(f"SKIP {doc_id}: no text in daemon response")
            continue
        path = OBS_DIR / f"{doc_id}-{slug_from(text, doc_id)}.md"
        if path.exists():
            print(f"EXISTS {path.name}")
            continue
        path.write_text(BANNER + text.rstrip() + "\n")
        print(f"WROTE {path.name}")


if __name__ == "__main__":
    main()
