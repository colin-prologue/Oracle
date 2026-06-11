<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-021 — Post-hoc Assertion Tests for Non-Invocable Systems

**Date:** 2026-05-19
**Domain:** tooling
**Source Project:** Claude-Root
**Source:** Smoke harness design for /speckit.run (PR4, T039–T041) — the orchestrator's entry point is a Claude Code slash command, not a shell-invocable script, so the smoke bats tests could not invoke it directly.

### Philosophy
When a system under test cannot be invoked programmatically from a test runner, structure smoke tests as post-hoc artifact assertions gated on an env-var pointing to a prior manual run. The test becomes a checker (did the prior invocation produce conforming outputs?) not a runner (does invoking now produce correct outputs?).

### Why I Hold This
The smoke harness for /speckit.run needed to assert FR-006 schema conformance, ADR-016 MUST-coalesce, and sidecar-canonical reconciliation against real subagent output — but /speckit.run is a Claude Code slash command with no shell-invocable equivalent. The only honest design was to check artifacts left by a prior manual invocation, skip cleanly without them, and document the env-var protocol. Coupling the test to the invocation mechanism would either require a brittle shell wrapper around the CLI or fake the exact failure mode the smoke tier exists to catch.

### Where It Applies
Any system whose primary entry point is interactive, conversational, or GUI-adjacent: CLI tools with interactive modes, LLM slash commands, browser-driven workflows, approval-gated pipelines. The pattern also applies when the invocation mechanism is prohibitively expensive (real money, rate limits) and must be run on a different cadence from the assertion checks.

### Known Tensions
Post-hoc tests decouple the run from the assertion, creating a window where the test suite passes against stale artifacts. Mitigations: env-var names that are specific to a fixture run (SMOKE_FEATURE_DIR, SMOKE_HALT_FEATURE_DIR), documenting the prerequisite invocation in the test file header, and treating the skip-count as a signal that no smoke run has been done.

### Open to Revision When
A programmatic invocation path exists (e.g., a headless CLI mode, a REST API, a record-and-replay mechanism) that can be called from a test runner with acceptable cost and flakiness. At that point, the post-hoc pattern should be replaced with a conventional setup→invoke→assert structure.
