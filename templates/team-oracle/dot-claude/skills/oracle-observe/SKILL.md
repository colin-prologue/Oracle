---
name: oracle-observe
description: Capture an impromptu observation (OBS) — fit-checks against existing records, drafts a descriptive pattern with cited instances, writes it on a branch and opens a lightweight PR. Invoked via /oracle-observe "[insight]".
---

# Capture an Observation (OBS)

Resolve `ORACLE_ROOT` (env var; default `~/team-oracle`). All writes go there.

## Arguments

`$ARGUMENTS` is the observed insight. If empty, ask what was observed.

## Execution

1. **Fit check.** Load `INDEX.md` (prefer `git show origin/main:INDEX.md`) and
   open any records whose hooks relate. Report: what's already covered, what
   this adds, which existing IDs it should cross-reference. If it's fully
   covered, say so and stop.

2. **Admission test.** An OBS must cite ≥2 dated instances (project + date +
   what occurred) and stay descriptive. If it prescribes ("we should..."),
   split it: keep the observed pattern here, route the prescription to
   `/oracle-debate`. If only one instance exists, offer to park the draft in
   `inbox/` until a second one shows up.

3. **Allocate the ID.** Max OBS-NNN across local `records/obs/` and
   `origin/main:INDEX.md`, +1. INDEX.md merge conflicts arbitrate races.

4. **Draft** using `records/_templates/obs-template.md`, `Status: active`.
   Present for curation; the user edits or approves.

5. **Write and propose.** On a new branch in `$ORACLE_ROOT`: write
   `records/obs/OBS-{NNN}-{slug}.md`, add its INDEX.md line, commit, push,
   open a PR titled `OBS-{NNN}: {title}`. OBS review is lightweight — the
   reviewer checks the instances are real and it isn't a duplicate, not
   whether they agree with any implied conclusion.
