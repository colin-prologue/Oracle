## PHI-004 — Validate Safety Nets Against Actual Workflow, Not Intended Workflow

**Date:** 2026-04-18
**Domain:** process
**Source:** PreCompact hook was the designed fallback for oracle retention, but real workflow uses `/clear` which bypasses PreCompact entirely. The gap existed silently until we traced the full hook trigger map.

### Philosophy
Safety nets must be validated against the workflow you actually run, not the workflow you designed for. A fallback that doesn't fire in practice offers false assurance — and the gap only surfaces when you trace the real execution path.

### Why I Hold This
We built the oracle retention system with PreCompact as a safety net. It looked complete on paper. The silent failure was that the actual workflow (`/clear`) bypasses PreCompact entirely — a different command, a different hook surface. Sessions were ending with no retention happening, and nothing indicated it.

### Where It Applies
Any system with fallback or safety mechanisms: backup scripts, retry logic, crash recovery, audit hooks, session-end protocols. The question isn't "does the fallback exist?" but "does the fallback fire in the code paths that actually run?"

### Known Tensions
Tracing every real execution path is expensive and may not be worth it for low-stakes fallbacks. The cost of validation scales with the cost of silent failure — prioritize validating fallbacks where silent failure is hard to detect.

### Open to Revision When
If tooling surfaces automatic validation of hook coverage (e.g., test harnesses that replay real workflows and assert which hooks fired), the manual trace step becomes automatable and this philosophy may narrow to "define the test, not the trace."
