---
name: oracle-preclear
description: Run before /clear or closing a session — scans the conversation for oracle-worthy content, proposes 0-3 PHI/OBS candidates for rapid yes/skip approval, and routes approved ones to the capture skills or the inbox. No argument needed.
---

# Pre-Clear Capture Scan

`/clear` drops session context with no hook to save it. This skill is the
manual retention path: run it first, then clear.

Resolve `ORACLE_ROOT` (env var; default `~/team-oracle`).

## Execution

1. **Orient.** Load `INDEX.md` (prefer `git show origin/main:INDEX.md`) so
   proposals dedupe against what the corpus already holds.

2. **Scan this conversation** for cross-project signal only:
   - held opinions argued or applied (PHI candidates — would they change the
     team's default on a new project?)
   - patterns with concrete instances (OBS candidates)
   - Exclude: project-specific facts the project repo already records, and
     anything confidential to the current project.

3. **Propose 0-3 candidates**, each as: type, one-line title, two-sentence
   gist, and why it clears the admission bar. Zero candidates is a valid
   outcome — say "nothing oracle-worthy this session" and stop. Ask per
   candidate: **yes / skip / edit**.

4. **For each approved candidate**, route by depth of attention available:
   - User has a few minutes → run the full `/oracle-debate` or
     `/oracle-observe` flow now (branch + PR).
   - User is wrapping up → write the draft to `$ORACLE_ROOT/inbox/` in the
     miner's candidate format for later `/oracle-triage`. Capture must not
     race the user's exit; the inbox absorbs the difference.

5. **Confirm:** "Captured N (PRs: ..., inbox: ...). Safe to /clear."
