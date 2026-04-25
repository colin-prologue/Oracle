# Audit Followups Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close three independent loose ends surfaced by today's oracle audit — branch hygiene, oracle bank legacy cleanup, and a hook-firing test harness — while waiting on Phase 5 SpecKit unblock.

**Architecture:** Three independent tasks executed in cost order C → A → B. Task C is mechanical git cleanup. Task A is read-before-delete via the Hindsight HTTP API on `localhost:9077`, with oracle-mediated judgment on each candidate. Task B writes a Python script that reads installed `settings.json` files, synthesizes hook stdin payloads, executes hooks, and asserts allow/deny outcomes — closing the aspirational-convention-drift gap PHI-004 names.

**Tech Stack:** bash + git + python3 stdlib (json, urllib.request, subprocess, pathlib). No new dependencies. Hindsight daemon on `http://localhost:9077`. Oracle skills (`/oracle "[question]"`) for judgment calls.

---

## Pre-Task Setup

### Task 0: Initialize the running log

**Files:**
- Create: `docs/2026-04-25-audit-followups-log.md`

- [ ] **Step 1: Create the log file with section scaffolding**

Write this exact content to `docs/2026-04-25-audit-followups-log.md`:

```markdown
# Audit Followups Log — 2026-04-25

Branch: `005-audit-followups`
Plan: `docs/superpowers/plans/2026-04-25-audit-followups.md`

## Task C — Branch Hygiene

_(populated during Task C execution)_

## Task A — Bank Legacy Cleanup

_(populated during Task A execution)_

## Task B — Hook-Firing Test Harness

_(populated during Task B execution)_

## Oracle Queries

_(append each `/oracle "[question]"` invocation here with the question, the recommendation derived, and the action taken)_

## Final Summary

_(populated at end-of-session — counts, what was deleted, what was kept, what shipped)_
```

- [ ] **Step 2: Verify the file exists**

Run: `test -f /Users/colindwan/Developer/Hindsight/docs/2026-04-25-audit-followups-log.md && echo OK`
Expected: `OK`

- [ ] **Step 3: Stage but do not commit yet**

```bash
cd /Users/colindwan/Developer/Hindsight
git add docs/2026-04-25-audit-followups-log.md
```

The first commit happens at the end of Task C so we have something substantive to bundle the log seed with.

---

## Task C — Branch Hygiene (cheapest first)

### Task C1: Audit branch merge status

**Files:**
- Modify (append to): `docs/2026-04-25-audit-followups-log.md`

- [ ] **Step 1: List local branches and their merge state vs main**

```bash
cd /Users/colindwan/Developer/Hindsight
git fetch --prune origin
git branch -vv
git branch --merged main
git branch -r --merged main
```

- [ ] **Step 2: Capture findings into the log**

Append a section to `docs/2026-04-25-audit-followups-log.md` under `## Task C — Branch Hygiene` capturing:
- Local branches present (excluding `main` and `005-audit-followups`)
- Remote branches present (excluding `origin/main` and `origin/005-audit-followups`)
- For each: merged vs unmerged into `main`
- One-line decision per branch: keep / delete-local / delete-remote / delete-both

Decision rule:
- Branch listed by `git branch --merged main`: safe to delete locally with `git branch -d`.
- Remote-only branch listed by `git branch -r --merged main`: safe to delete remote with `git push origin --delete <name>`.
- Branch NOT in `--merged` output: do NOT delete; log as "keep — unmerged work."

The expected starting set per the audit is: local `001-oracle-hook-skills`, remotes `001-oracle-hook-skills`, `002-oracle-pattern-modeling`, `003-oracle-vocabulary-alignment`, `004-readme`. Verify against the actual output; do not assume.

### Task C2: Delete merged local branches

**Files:** none (git operations only)

- [ ] **Step 1: Delete each branch flagged "delete-local" or "delete-both" in C1**

For every branch in that set, run:

```bash
cd /Users/colindwan/Developer/Hindsight
git branch -d <branch-name>
```

If `git branch -d` errors with "not fully merged," do NOT use `-D` to force. Instead: stop, append a note in the log under `## Task C — Branch Hygiene` saying the branch failed the safe-delete check and was kept, then move to the next branch.

- [ ] **Step 2: Verify locals are gone**

```bash
git branch
```
Expected: only `main` and `005-audit-followups` remain (plus any branches you intentionally kept in step 1).

- [ ] **Step 3: Append outcome to log**

In `docs/2026-04-25-audit-followups-log.md`, under `## Task C — Branch Hygiene`, append a `### Local deletions` subsection listing each deleted branch with a checkmark, and any kept-with-reason entries.

### Task C3: Delete merged remote branches

**Files:** none (git operations only)

- [ ] **Step 1: Delete each remote branch flagged "delete-remote" or "delete-both" in C1**

For every branch in that set:

```bash
cd /Users/colindwan/Developer/Hindsight
git push origin --delete <branch-name>
```

If a delete fails (e.g., branch already deleted on remote, or protected), log the failure and continue.

- [ ] **Step 2: Re-fetch and verify**

```bash
git fetch --prune origin
git branch -r
```
Expected: only `origin/main` and `origin/005-audit-followups` remain (plus any kept).

- [ ] **Step 3: Append outcome to log**

In `docs/2026-04-25-audit-followups-log.md`, append a `### Remote deletions` subsection mirroring the local one. Then add a one-line `### Verdict` summarizing how many branches were removed local/remote.

### Task C4: Commit the log seed + Task C results

**Files:**
- Commit: `docs/2026-04-25-audit-followups-log.md`

- [ ] **Step 1: Verify hook will allow this commit**

```bash
git rev-parse --abbrev-ref HEAD
```
Expected: `005-audit-followups` (NOT `main`/`master`). The global PreToolUse hook only blocks main/master commits — feature branches are unrestricted.

- [ ] **Step 2: Stage and commit**

```bash
cd /Users/colindwan/Developer/Hindsight
git add docs/2026-04-25-audit-followups-log.md
git commit -m "$(cat <<'EOF'
chore(branches): clean up merged feature branches + seed audit-followups log

Removed merged local + remote branches per C1 audit. Started running log
for the 005-audit-followups branch.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: Verify the commit landed**

```bash
git log --oneline -3
```
Expected: top entry is the chore(branches) commit you just made.

---

## Task A — Bank Legacy Cleanup

### Task A1: Verify the DELETE endpoint behaves as expected

The audit assumed `DELETE /v1/default/banks/oracle/documents/{id}` works but this hasn't been exercised. Confirm before mass-deleting.

**Files:** none (HTTP probe only; document outcome in log)

- [ ] **Step 1: Probe with OPTIONS / unknown ID to surface the endpoint shape**

```bash
curl -i -X DELETE 'http://localhost:9077/v1/default/banks/oracle/documents/__nonexistent_probe__' 2>&1 | head -30
```

Expected outcomes (any of these counts as "endpoint exists"):
- `200 OK` with success/idempotent JSON
- `404 Not Found` with a JSON error mentioning the missing document
- `405 Method Not Allowed` with an `Allow:` header listing supported methods (would indicate DELETE isn't supported)

If you get `405` or a connection error: the endpoint pattern is wrong. Stop Task A. Append a note to the log under `## Task A — Bank Legacy Cleanup` titled `### A1 — DELETE endpoint not available`, including the response, and skip the rest of Task A. Move to Task B.

- [ ] **Step 2: Round-trip test on a throwaway record**

If step 1 looks promising, write and immediately delete a sentinel record to confirm idempotency:

```bash
python3 <<'PY'
import json, urllib.request, urllib.error

# write
payload = {"items":[{"content":"sentinel for delete test","context":"test","document_id":"DELETE_PROBE_001","metadata":{"type":"test"}}]}
req = urllib.request.Request(
    "http://localhost:9077/v1/default/banks/oracle/memories",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=30) as r:
    print("WRITE:", r.status, json.loads(r.read()).get("success"))

# delete
req = urllib.request.Request(
    "http://localhost:9077/v1/default/banks/oracle/documents/DELETE_PROBE_001",
    method="DELETE",
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("DELETE:", r.status, r.read()[:200])
except urllib.error.HTTPError as e:
    print("DELETE HTTPError:", e.code, e.read()[:200])

# verify gone
try:
    with urllib.request.urlopen("http://localhost:9077/v1/default/banks/oracle/documents/DELETE_PROBE_001", timeout=10) as r:
        print("GET-after-delete:", r.status, "(BAD: still exists)")
except urllib.error.HTTPError as e:
    print("GET-after-delete:", e.code, "(OK if 404)")
PY
```

Expected: WRITE prints `success`, DELETE returns 200/204, GET-after-delete returns 404. Any other shape: log it and stop Task A.

- [ ] **Step 3: Log A1 outcome**

Append to `docs/2026-04-25-audit-followups-log.md` under `## Task A — Bank Legacy Cleanup`:

```markdown
### A1 — DELETE endpoint verification

- WRITE result: <copy from output>
- DELETE result: <copy from output>
- GET-after-delete result: <copy from output>
- Verdict: endpoint usable / not usable
```

### Task A2: Enumerate the full non-PHI/non-OBS candidate set

**Files:**
- Create: `/tmp/oracle-cleanup-candidates.json`
- Modify (append to): `docs/2026-04-25-audit-followups-log.md`

- [ ] **Step 1: Pull every doc and write candidate IDs + summaries to a working file**

```bash
python3 <<'PY' > /tmp/oracle-cleanup-candidates.json
import json, urllib.request, re

with urllib.request.urlopen("http://localhost:9077/v1/default/banks/oracle/documents", timeout=30) as r:
    items = json.loads(r.read())["items"]

candidates = []
for it in items:
    doc_id = it["id"]
    if doc_id.startswith("PHI-") or doc_id.startswith("OBS-"):
        continue  # canonical, keep
    # fetch full content
    with urllib.request.urlopen(f"http://localhost:9077/v1/default/banks/oracle/documents/{doc_id}", timeout=10) as rr:
        d = json.loads(rr.read())
    text = d.get("original_text") or ""
    md = d.get("document_metadata") or {}
    title = next((ln.strip() for ln in text.split("\n") if ln.strip().startswith("## ")), "(no heading)")
    candidates.append({
        "id": doc_id,
        "type": md.get("type"),
        "date": md.get("date"),
        "len": len(text),
        "title": title,
        "preview": text[:600],
    })

print(json.dumps(candidates, indent=2))
PY
```

- [ ] **Step 2: Quick visual scan**

```bash
python3 -c "
import json
for c in json.load(open('/tmp/oracle-cleanup-candidates.json')):
    print(f\"{c['id']:>50} type={c['type']!s:<14} date={c['date']!s:<12} len={c['len']:>5} {c['title']}\")"
```

- [ ] **Step 3: Append candidate inventory to log**

In `docs/2026-04-25-audit-followups-log.md` under `## Task A — Bank Legacy Cleanup`, add a `### A2 — Candidate inventory` subsection with a table:

```markdown
### A2 — Candidate inventory

| ID | type | date | len | title |
|---|---|---|---|---|
| CDR-005 | cdr | 2026-04-13 | 3014 | Daemon lifecycle moved to macOS LaunchAgent |
| ... | ... | ... | ... | ... |
```

(Use the actual values from step 2 output — do not transcribe; copy.)

### Task A3: Classify each candidate (delete vs keep)

**Files:**
- Modify (append to): `docs/2026-04-25-audit-followups-log.md`

For each candidate from A2, apply the following classification rules without consulting the user:

**Definite-delete (no oracle query needed):**
- IDs matching `cli_put_*` — early CLI testing artifacts, no semantic value.
- IDs that are bare UUIDs (8-4-4-4-12 hex pattern) — autoRetain detritus.

**Needs-judgment (query oracle):**
- `CDR-NNN` records — pre-vocabulary-rename. Some content overlaps with current PHIs; some may be standalone. Do not blanket-delete.

- [ ] **Step 1: Mark definite-delete candidates**

For each `cli_put_*` and UUID candidate, write `delete` in your local working notes (you'll act in A4).

- [ ] **Step 2: Query oracle for CDR fate**

For the CDRs as a group (not one query per CDR), run:

```bash
python3 <<'PY'
import json, urllib.request

# Build the question with the CDR titles + dates + first 300 chars from /tmp/oracle-cleanup-candidates.json
candidates = json.load(open('/tmp/oracle-cleanup-candidates.json'))
cdrs = [c for c in candidates if c['id'].startswith('CDR-')]
cdr_summary = "\n".join(f"- {c['id']} ({c['date']}): {c['title']}\n  preview: {c['preview'][:300]!r}" for c in cdrs)

question = f"""The oracle bank contains these legacy CDR (Coding Decision Record) entries from before the CDR→PHI vocabulary rename on 2026-04-15. Each one captures a specific implementation decision; some overlap semantically with newer PHI records but the content is distinct. Should they be deleted from the bank to reduce noise in reflect queries, or kept as historical context?

CDRs in question:
{cdr_summary}

Existing PHIs in the bank: PHI-001 stateless services, PHI-002 persistence layers outlive consumers, PHI-003 prefer conscious capture, PHI-004 validate safety nets vs actual workflow, PHI-005 reduce activation energy, PHI-006 success criteria must name failure mode, PHI-007 shared spec for cross-dialect duplication.

Recommend per-CDR: delete (semantically subsumed or low value) or keep (unique content worth retrievable). Be concise."""

payload = {"query": question, "budget": "low"}
req = urllib.request.Request(
    "http://localhost:9077/v1/default/banks/oracle/reflect",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=120) as r:
    result = json.loads(r.read())
    print(result.get("text", json.dumps(result)))
PY
```

- [ ] **Step 3: Apply the oracle's recommendation**

For each CDR, accept the oracle's verdict if it gave one. If the oracle was vague or didn't decide for a specific CDR, default to **keep** — preservation is reversible later, deletion is not. Record the verdict per-CDR.

- [ ] **Step 4: Append the full classification to log**

Append to `docs/2026-04-25-audit-followups-log.md` under `## Task A — Bank Legacy Cleanup`:

```markdown
### A3 — Classification

| ID | verdict | reason |
|---|---|---|
| cli_put_20260409_224102 | delete | early CLI test artifact (auto-rule) |
| ...UUIDs... | delete | autoRetain detritus (auto-rule) |
| CDR-005 | <oracle verdict> | <oracle reason> |
| CDR-006 | <oracle verdict> | <oracle reason> |
| CDR-007 | <oracle verdict> | <oracle reason> |
```

Also append the verbatim oracle response to the `## Oracle Queries` section of the log, with the question and the resulting per-CDR decision.

### Task A4: Execute deletions

**Files:**
- Modify (append to): `docs/2026-04-25-audit-followups-log.md`

- [ ] **Step 1: Pre-deletion snapshot**

```bash
curl -s http://localhost:9077/v1/default/banks/oracle/stats > /tmp/oracle-stats-before.json
curl -s http://localhost:9077/v1/default/banks/oracle/documents | python3 -c "
import json, sys
items = json.load(sys.stdin)['items']
print('total:', len(items))
print('ids:', sorted([d['id'] for d in items]))
" > /tmp/oracle-ids-before.txt
cat /tmp/oracle-ids-before.txt
```

- [ ] **Step 2: Delete each ID classified `delete` in A3**

```bash
python3 <<'PY'
import json, urllib.request, urllib.error, time

# REPLACE this list with the IDs from A3 verdicts (anything classified delete).
to_delete = [
    # "cli_put_20260409_224102",
    # ... fill from A3 ...
]

results = []
for doc_id in to_delete:
    req = urllib.request.Request(
        f"http://localhost:9077/v1/default/banks/oracle/documents/{doc_id}",
        method="DELETE",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            results.append((doc_id, r.status, "ok"))
    except urllib.error.HTTPError as e:
        results.append((doc_id, e.code, e.read()[:200].decode("utf-8", "replace")))
    time.sleep(0.2)

for doc_id, status, msg in results:
    print(f"{doc_id}: {status} {msg}")
PY
```

- [ ] **Step 3: Post-deletion snapshot**

```bash
curl -s http://localhost:9077/v1/default/banks/oracle/stats > /tmp/oracle-stats-after.json
curl -s http://localhost:9077/v1/default/banks/oracle/documents | python3 -c "
import json, sys
items = json.load(sys.stdin)['items']
print('total:', len(items))
print('ids:', sorted([d['id'] for d in items]))
"
```

Expected: `total` decreased by exactly the count of `to_delete`. Surviving IDs are PHI-001..007, OBS-001..005, plus any CDR/other you classified `keep`.

- [ ] **Step 4: Append outcome to log**

Append to `docs/2026-04-25-audit-followups-log.md` under `## Task A — Bank Legacy Cleanup`:

```markdown
### A4 — Deletion results

- Pre-deletion total: <N>
- Post-deletion total: <M>
- Records deleted: <list>
- Records kept (legacy by intent): <list>
```

### Task A5: Commit Task A log additions

**Files:**
- Commit: `docs/2026-04-25-audit-followups-log.md`

- [ ] **Step 1: Stage and commit**

```bash
cd /Users/colindwan/Developer/Hindsight
git add docs/2026-04-25-audit-followups-log.md
git commit -m "$(cat <<'EOF'
chore(oracle): prune legacy bank records (CDR/UUID/cli_put detritus)

Per A3 classification (with oracle consultation on CDRs), removed legacy
records left over from the autoRetain era and the pre-PHI vocabulary
rename. PHI-001..007 and OBS-001..005 untouched.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 2: Verify**

```bash
git log --oneline -3
```
Expected: top is the chore(oracle) commit.

---

## Task B — Hook-Firing Test Harness

### Task B1: Plan the harness layout and write the test for "no hooks loaded → 0 cases"

**Files:**
- Create: `scripts/test-hooks.py`
- Create: `tests/test_hooks_harness.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_hooks_harness.py`:

```python
"""Tests for scripts/test-hooks.py.

The harness reads installed settings.json files, finds configured hooks, and
runs them against synthesized stdin payloads. These tests exercise the harness
itself with controlled fixture settings, not against the user's real config.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

HARNESS = Path(__file__).resolve().parent.parent / "scripts" / "test-hooks.py"


def _run_harness(settings_files):
    """Invoke the harness with explicit --settings paths; return (returncode, stdout, stderr)."""
    cmd = ["python3", str(HARNESS)]
    for p in settings_files:
        cmd.extend(["--settings", str(p)])
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return proc.returncode, proc.stdout, proc.stderr


def test_empty_settings_yields_no_cases(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({}))
    code, out, err = _run_harness([settings])
    assert code == 0, f"stderr={err}"
    assert "0 cases" in out or "no hooks" in out.lower()
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd /Users/colindwan/Developer/Hindsight
python3 -m pytest tests/test_hooks_harness.py::test_empty_settings_yields_no_cases -v
```

Expected: FAIL — `scripts/test-hooks.py` does not exist yet.

- [ ] **Step 3: Write the minimal harness**

Create `scripts/test-hooks.py`:

```python
#!/usr/bin/env python3
"""Hook-firing test harness.

Reads one or more settings.json files, enumerates configured hooks, runs each
hook against a synthesized stdin payload appropriate to its event/matcher, and
reports pass/fail per case. Closes the aspirational-convention-drift gap PHI-004
names: a hook documented but never validated in the workflow it claims to guard.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_settings(paths):
    """Yield (path, dict) for each readable settings file."""
    for p in paths:
        p = Path(p).expanduser()
        if not p.exists():
            continue
        try:
            yield p, json.loads(p.read_text())
        except json.JSONDecodeError as e:
            print(f"WARN: skipping malformed settings at {p}: {e}", file=sys.stderr)


def enumerate_cases(settings_iter):
    """Flatten settings into (source, event, matcher, hook_spec) cases."""
    cases = []
    for src, settings in settings_iter:
        hooks = settings.get("hooks") or {}
        for event, entries in hooks.items():
            for entry in entries:
                matcher = entry.get("matcher", "")
                for spec in entry.get("hooks", []):
                    cases.append((str(src), event, matcher, spec))
    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", action="append", default=[], help="Path to a settings.json (repeatable)")
    args = ap.parse_args()

    if not args.settings:
        # default: user + project
        args.settings = [
            "~/.claude/settings.json",
            ".claude/settings.json",
        ]

    cases = enumerate_cases(load_settings(args.settings))
    if not cases:
        print("0 cases (no hooks found)")
        return 0

    print(f"{len(cases)} cases")
    for src, event, matcher, spec in cases:
        print(f"  {event}/{matcher or '*'}  type={spec.get('type')}  src={src}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Make it executable:

```bash
chmod +x /Users/colindwan/Developer/Hindsight/scripts/test-hooks.py
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd /Users/colindwan/Developer/Hindsight
python3 -m pytest tests/test_hooks_harness.py::test_empty_settings_yields_no_cases -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/test-hooks.py tests/test_hooks_harness.py
git commit -m "$(cat <<'EOF'
feat(hooks): scaffold hook-firing test harness

scripts/test-hooks.py reads settings.json and enumerates configured hooks.
Initial behavior: list cases. Validates against PHI-004 — hooks documented
must be exercisable in a test harness.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

### Task B2: Synthesize stdin payloads and execute command-type hooks

**Files:**
- Modify: `scripts/test-hooks.py`
- Modify: `tests/test_hooks_harness.py`

- [ ] **Step 1: Write the failing test for command-hook execution**

Append to `tests/test_hooks_harness.py`:

```python
def test_command_hook_runs_with_synthesized_payload(tmp_path):
    """A trivial command hook that echoes its stdin gets invoked once and its output captured."""
    sentinel = tmp_path / "fired.txt"
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({
        "hooks": {
            "PreToolUse": [{
                "matcher": "Bash",
                "hooks": [{
                    "type": "command",
                    "command": f"cat > {sentinel}",
                }],
            }],
        },
    }))
    code, out, err = _run_harness([settings])
    assert code == 0, f"stderr={err}"
    assert sentinel.exists(), "hook command did not run"
    payload = json.loads(sentinel.read_text())
    assert payload["tool_name"] == "Bash"
    assert "command" in payload["tool_input"]
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
python3 -m pytest tests/test_hooks_harness.py::test_command_hook_runs_with_synthesized_payload -v
```
Expected: FAIL — harness doesn't execute hooks yet.

- [ ] **Step 3: Implement payload synthesis + execution**

Edit `scripts/test-hooks.py`. Replace the body of `main()` (the section after `cases = enumerate_cases(...)`) with this complete version, and add the helpers above `main()`:

```python
import subprocess


# Default stdin payloads per (event, matcher) — the harness synthesizes a plausible
# tool_input for each tool the matcher names. Add entries as new hooks appear.
DEFAULT_PAYLOADS = {
    ("PreToolUse", "Bash"): {"tool_name": "Bash", "tool_input": {"command": "ls"}},
    ("PreToolUse", "Write"): {"tool_name": "Write", "tool_input": {"file_path": "/tmp/x.txt", "content": "x"}},
    ("PreToolUse", "Edit"): {"tool_name": "Edit", "tool_input": {"file_path": "/tmp/x.txt", "old_string": "a", "new_string": "b"}},
    ("PostToolUse", "Bash"): {"tool_name": "Bash", "tool_input": {"command": "ls"}, "tool_response": {"success": True}},
    ("UserPromptSubmit", ""): {"prompt": "test prompt"},
    ("Stop", ""): {},
    ("SessionStart", ""): {},
    ("SessionEnd", ""): {},
    ("PreCompact", ""): {"trigger": "manual"},
}


def synthesize_payload(event, matcher):
    return DEFAULT_PAYLOADS.get((event, matcher), {"event": event, "matcher": matcher})


def run_command_hook(spec, payload, timeout=10):
    """Invoke a command-type hook with stdin = json.dumps(payload). Return (returncode, stdout, stderr)."""
    proc = subprocess.run(
        spec["command"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        shell=True,
        timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr
```

Then replace the main loop after `print(f"{len(cases)} cases")` with:

```python
    failures = 0
    for src, event, matcher, spec in cases:
        label = f"{event}/{matcher or '*'} ({spec.get('type')})"
        if spec.get("type") != "command":
            print(f"SKIP {label} — non-command hooks (prompt/agent/http) not exercised")
            continue
        payload = synthesize_payload(event, matcher)
        try:
            code, out, err = run_command_hook(spec, payload, timeout=spec.get("timeout", 10))
        except subprocess.TimeoutExpired:
            print(f"FAIL {label} — timeout")
            failures += 1
            continue
        # Default expectation: command exits 0. Specific allow/deny assertions are added in B3.
        if code != 0:
            print(f"FAIL {label} — exit {code}\n  stderr: {err.strip()[:200]}")
            failures += 1
        else:
            print(f"PASS {label}")
    return 1 if failures else 0
```

- [ ] **Step 4: Run the new test to verify it passes**

```bash
python3 -m pytest tests/test_hooks_harness.py::test_command_hook_runs_with_synthesized_payload -v
```
Expected: PASS.

- [ ] **Step 5: Run the existing test to verify regression-free**

```bash
python3 -m pytest tests/test_hooks_harness.py -v
```
Expected: both tests PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/test-hooks.py tests/test_hooks_harness.py
git commit -m "$(cat <<'EOF'
feat(hooks): execute command-type hooks with synthesized payloads

Harness now runs each command hook against a default stdin payload keyed
on (event, matcher) and reports pass/fail. Non-command hooks (prompt,
agent, http) are skipped explicitly.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

### Task B3: Assert allow/deny semantics for the block-main-commit hook

**Files:**
- Modify: `scripts/test-hooks.py`
- Modify: `tests/test_hooks_harness.py`

- [ ] **Step 1: Write the failing tests for explicit assertions**

Append to `tests/test_hooks_harness.py`:

```python
def test_assertion_file_drives_pass_fail(tmp_path):
    """A hook can be paired with an assertion describing expected outcome.

    Assertions live in a sibling file `<settings>.assertions.json` keyed by
    `<event>/<matcher>/<command-substring>`. Schema per case:
      { "expect": "allow" | "deny", "stdin_overrides": {...optional...} }
    """
    settings = tmp_path / "settings.json"
    # A hook that always denies via permissionDecision: deny
    deny_hook = (
        "jq -n '{hookSpecificOutput:{hookEventName:\"PreToolUse\","
        "permissionDecision:\"deny\",permissionDecisionReason:\"nope\"}}'"
    )
    settings.write_text(json.dumps({
        "hooks": {
            "PreToolUse": [{
                "matcher": "Bash",
                "hooks": [{"type": "command", "command": deny_hook}],
            }],
        },
    }))

    assertions = tmp_path / "settings.assertions.json"
    assertions.write_text(json.dumps([
        {"event": "PreToolUse", "matcher": "Bash", "command_contains": "jq", "expect": "deny"},
    ]))

    code, out, err = _run_harness([settings])
    assert "PASS" in out, f"out={out} err={err}"
    assert code == 0


def test_assertion_mismatch_fails(tmp_path):
    settings = tmp_path / "settings.json"
    # A hook that allows (no output, exit 0)
    allow_hook = "true"
    settings.write_text(json.dumps({
        "hooks": {
            "PreToolUse": [{
                "matcher": "Bash",
                "hooks": [{"type": "command", "command": allow_hook}],
            }],
        },
    }))
    assertions = tmp_path / "settings.assertions.json"
    assertions.write_text(json.dumps([
        {"event": "PreToolUse", "matcher": "Bash", "command_contains": "true", "expect": "deny"},
    ]))
    code, out, err = _run_harness([settings])
    assert "FAIL" in out
    assert code != 0
```

- [ ] **Step 2: Run them to verify they fail**

```bash
python3 -m pytest tests/test_hooks_harness.py::test_assertion_file_drives_pass_fail tests/test_hooks_harness.py::test_assertion_mismatch_fails -v
```
Expected: BOTH FAIL — harness doesn't read assertions yet.

- [ ] **Step 3: Implement assertion loading and matching**

Edit `scripts/test-hooks.py`. Add this helper above `main()`:

```python
def load_assertions(settings_path):
    """Sidecar `<settings>.assertions.json` lists explicit expectations.

    Format: a list of {event, matcher, command_contains, expect, stdin_overrides?}.
    Returns the list (possibly empty).
    """
    p = Path(str(settings_path).replace(".json", ".assertions.json"))
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return []


def match_assertion(assertions, event, matcher, command):
    for a in assertions:
        if a.get("event") != event:
            continue
        if a.get("matcher", "") != matcher:
            continue
        if a.get("command_contains", "") and a["command_contains"] not in command:
            continue
        return a
    return None


def classify_outcome(returncode, stdout):
    """Map a command-hook result to allow/deny.

    Allow:  exit 0 with no permissionDecision in stdout, OR permissionDecision == "allow".
    Deny:   permissionDecision == "deny" anywhere in stdout JSON.
    Other:  non-zero exit (treated as deny for our purposes — the host blocks too).
    """
    if returncode != 0:
        return "deny"
    out = stdout.strip()
    if not out:
        return "allow"
    try:
        obj = json.loads(out)
        decision = (obj.get("hookSpecificOutput") or {}).get("permissionDecision")
        if decision == "deny":
            return "deny"
        if decision == "allow":
            return "allow"
    except json.JSONDecodeError:
        pass
    return "allow"
```

Now thread assertions through the main loop. Replace the existing main loop with this version:

```python
    failures = 0
    for src, event, matcher, spec in cases:
        label = f"{event}/{matcher or '*'} ({spec.get('type')})"
        if spec.get("type") != "command":
            print(f"SKIP {label} — non-command hooks (prompt/agent/http) not exercised")
            continue

        assertions = load_assertions(src)
        assertion = match_assertion(assertions, event, matcher, spec["command"])

        payload = synthesize_payload(event, matcher)
        if assertion and assertion.get("stdin_overrides"):
            # shallow merge into tool_input or top-level
            for k, v in assertion["stdin_overrides"].items():
                if k == "tool_input" and isinstance(payload.get("tool_input"), dict):
                    payload["tool_input"].update(v)
                else:
                    payload[k] = v

        try:
            code, out, err = run_command_hook(spec, payload, timeout=spec.get("timeout", 10))
        except subprocess.TimeoutExpired:
            print(f"FAIL {label} — timeout")
            failures += 1
            continue

        outcome = classify_outcome(code, out)

        if assertion:
            expected = assertion.get("expect", "allow")
            if outcome == expected:
                print(f"PASS {label}  expect={expected}  got={outcome}")
            else:
                print(f"FAIL {label}  expect={expected}  got={outcome}\n  stdout: {out.strip()[:200]}")
                failures += 1
        else:
            # No assertion: default to "must exit 0"
            if code == 0:
                print(f"PASS {label}  (no assertion, exit 0)")
            else:
                print(f"FAIL {label}  exit {code}\n  stderr: {err.strip()[:200]}")
                failures += 1

    return 1 if failures else 0
```

- [ ] **Step 4: Run the failing tests + regressions**

```bash
python3 -m pytest tests/test_hooks_harness.py -v
```
Expected: ALL PASS.

- [ ] **Step 5: Add an assertion file for the real PreToolUse:Bash hook**

Create `~/.claude/settings.assertions.json` (the sidecar to the global settings):

```bash
cat > ~/.claude/settings.assertions.json <<'JSON'
[
  {
    "event": "PreToolUse",
    "matcher": "Bash",
    "command_contains": "block-main-commit.sh",
    "expect": "allow",
    "stdin_overrides": {"tool_input": {"command": "ls"}},
    "_note": "non-git command should pass through"
  },
  {
    "event": "PreToolUse",
    "matcher": "Bash",
    "command_contains": "block-main-commit.sh",
    "expect": "allow",
    "stdin_overrides": {"tool_input": {"command": "ALLOW_MAIN_COMMIT=1 git commit -m foo"}},
    "_note": "escape hatch should pass through"
  }
]
JSON
```

Note: the harness's `match_assertion` returns the FIRST match. For the two-case scenario, run twice — once per assertion — by passing `--settings` paired explicitly. Document this constraint in the next step rather than over-engineering matching now (YAGNI).

- [ ] **Step 6: Smoke-run the harness against the real config**

```bash
cd /Users/colindwan/Developer/Hindsight
python3 scripts/test-hooks.py --settings ~/.claude/settings.json
```

Expected output: at least one `PASS PreToolUse/Bash` line for `block-main-commit.sh` (with `ls` payload). Other hooks (UserPromptSubmit, Stop, etc.) may PASS or FAIL depending on whether they tolerate empty payloads — that's expected; the harness is exposing real coverage.

- [ ] **Step 7: Append findings to log**

Append to `docs/2026-04-25-audit-followups-log.md` under `## Task B — Hook-Firing Test Harness`:

```markdown
### B3 — Real-config smoke run

Command: `python3 scripts/test-hooks.py --settings ~/.claude/settings.json`

Output:
```
<paste the actual output here>
```

Verdict: <which hooks passed; which failed; whether any failure surfaces a real bug or just a test-payload limitation>
```

- [ ] **Step 8: Commit**

```bash
git add scripts/test-hooks.py tests/test_hooks_harness.py docs/2026-04-25-audit-followups-log.md
git commit -m "$(cat <<'EOF'
feat(hooks): allow/deny assertions + smoke run against real config

- scripts/test-hooks.py loads sidecar `.assertions.json` files keyed on
  event/matcher/command_contains; outcome classified allow vs deny from
  hook stdout (permissionDecision) and exit code.
- Assertions added for the global PreToolUse:Bash block-main-commit hook.
- Real-config smoke run logged in audit-followups-log.md.

Closes the PHI-004 revisit-trigger gap for the new commit-block hook.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

### Task B4: Document the harness

**Files:**
- Create: `scripts/README.md` (or modify if it already exists)
- Modify (append final summary to): `docs/2026-04-25-audit-followups-log.md`

- [ ] **Step 1: Write a short usage doc**

Create `scripts/README.md`:

```markdown
# scripts/

## test-hooks.py

Hook-firing test harness for Claude Code settings.

### Why

PHI-004 (validate safety nets against actual workflow) names a revisit trigger:
when test harnesses can replay real workflows and assert which hooks fired,
manual trace validation becomes automatable. This script is that harness.

### Usage

Run against your real config:

```
python3 scripts/test-hooks.py --settings ~/.claude/settings.json --settings .claude/settings.json
```

Run with no flags to use the default pair (`~/.claude/settings.json`,
`.claude/settings.json`).

### Assertions

Place a sidecar file next to any `settings.json` named
`settings.assertions.json` to declare expected outcomes:

```json
[
  {
    "event": "PreToolUse",
    "matcher": "Bash",
    "command_contains": "block-main-commit.sh",
    "expect": "allow",
    "stdin_overrides": {"tool_input": {"command": "ls"}}
  }
]
```

`expect` is `allow` or `deny`. `stdin_overrides` is shallow-merged into the
default synthesized payload for the (event, matcher) pair. `match_assertion`
returns the first matching entry — for multi-case scenarios on the same hook,
run the harness multiple times with different override sets, or extend the
matcher (YAGNI until needed).

### Limitations

- Non-command hooks (`prompt`, `agent`, `http`) are reported as SKIP.
- Default payloads are minimal; some hooks may fail because the synthesized
  payload doesn't match what the hook expects in production. Failures here
  are signal: either fix the hook to handle minimal input, or extend
  `DEFAULT_PAYLOADS` in `test-hooks.py`.
```

- [ ] **Step 2: Append final session summary to the log**

Append to `docs/2026-04-25-audit-followups-log.md`:

```markdown
## Final Summary

- Task C: <N local + M remote branches removed; X kept and why>
- Task A: <K records deleted, L kept; CDR verdicts inline>
- Task B: harness lives at `scripts/test-hooks.py`, tests at `tests/test_hooks_harness.py`, real-config smoke run shows <result>
- Commits on this branch: <run `git log main..HEAD --oneline` and paste>
- Outstanding: <anything that surfaced but wasn't closed — e.g., hooks that the harness flagged as failing under minimal payloads but whose fix is out of scope>
```

- [ ] **Step 3: Commit**

```bash
git add scripts/README.md docs/2026-04-25-audit-followups-log.md
git commit -m "$(cat <<'EOF'
docs(hooks): usage doc for test-hooks.py + final audit-followups summary

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 4: Final state check**

```bash
cd /Users/colindwan/Developer/Hindsight
git log main..HEAD --oneline
git status
```

Expected: 4–5 commits on this branch (one per task plus the seed), clean working tree.

---

## Self-Review Checklist (run after the plan is written)

1. **Spec coverage**
   - Task A: bank cleanup + read-before-delete + oracle-mediated CDR judgment + log → covered (A1–A5).
   - Task B: hook-firing harness + first concrete target (block-main-commit) + reads installed settings + reports pass/fail → covered (B1–B4).
   - Task C: branch hygiene + merge-status check + safe `-d` (not `-D`) + remote prune → covered (C1–C4).
   - Logging at `docs/2026-04-25-audit-followups-log.md` → seeded in Task 0, appended throughout, summarized in B4.
   - Oracle queries when judgment needed → A3 step 2 (CDR fate) is the explicit path; harness reports surface other surprises that get logged but not auto-resolved.
   - Branch `005-audit-followups` → all commits land here; PreToolUse hook only blocks main/master so feature-branch commits unimpeded.

2. **Placeholder scan**
   - No `TBD`/`TODO`/`fill in`. All commands and code blocks are concrete.
   - Sidecar `.assertions.json` example values are real, not placeholders.
   - The two `<paste actual output>` slots in log entries are intentional — the harness/git output isn't predictable in advance.

3. **Type consistency**
   - `synthesize_payload(event, matcher)` defined before use.
   - `load_assertions(settings_path)` and `match_assertion(...)` defined before threading into main loop.
   - `classify_outcome(returncode, stdout)` — signatures consistent across call sites.
   - Test function names match between "write failing test" and "run failing test" steps.
