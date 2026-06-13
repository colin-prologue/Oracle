<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

## OBS-014 — Pre-Dispatch State Snapshot for Delegated-Action Auditing

**Date:** 2026-05-16
**Source Project:** Claude-Root (spec 010 autonomous-workflow, run-check-sandbox.sh)

### Observation
Before delegating an action to an external agent or process, snapshot the observable state (git HEAD commit hash, filesystem digest, API cursor) into a location accessible to the post-action auditor. After the action completes, diff against the snapshot. This enables precision auditing of exactly what changed during the delegation — without relying on the delegate's self-report, which can omit or misrepresent.

### Grounding Instance
`run-check-sandbox.sh` reads `.run/pre-dispatch-head` (written by the orchestrator immediately before each subagent dispatch) and runs `git diff <pre-dispatch-head>..HEAD` to identify committed changes. Without the snapshot, the helper can only check uncommitted working-tree state; committed violations would be invisible. The pattern: snapshot → delegate → diff. The snapshot file lives in the run's own state directory (`.run/`), is written atomically before dispatch, and is consumed by the post-action auditor — not by the delegate itself.

### Where It Applies
Any orchestrator dispatching subagents or external workers where post-action auditing is required: CI runners dispatching jobs, IaC pipelines running `terraform apply`, agent orchestrators dispatching code-action subagents, workflow engines invoking external tools. The snapshot must be: (a) taken immediately before delegation starts, (b) stored in a location the auditor can read independently of the delegate, and (c) cheap enough to write that it doesn't become a bottleneck.

### Relationship to Existing Patterns
Extends ADR-013's inverted orchestration model (oracle bank): subagents write to canonical disk; orchestrator reads independently rather than trusting returned summaries. The snapshot is the pre-action complement — the post-action canonical write is the post-action complement. Together they bracket the delegation with independently verifiable state, eliminating the self-report trust requirement entirely.
