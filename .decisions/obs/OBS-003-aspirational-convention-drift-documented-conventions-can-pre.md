<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

OBS-003 — Aspirational Convention Drift: Documented Conventions Can Precede and Outlive Their Implementation

**Date:** 2026-04-18
**Derived from:** PHI-004, OBS-001 (Pattern 8)

---

Convention documents that describe required behavior in downstream consumers represent a unique drift category: the convention appears complete (docs written, tests passing) while the actual call sites do not exist. Unlike typical doc-code drift (where code exists but docs are wrong), aspirational convention drift means the documentation is ahead of the implementation.

**Why it is hard to detect:**
- The convention document is thorough and accurate in intent
- Associated tests may pass for the wrong reason (keyword presence vs. behavioral wiring)
- Code review checks the implementation — it cannot check for the absence of an implementation it never saw

**Discovery method:**
Cross-reference the convention's claimed call sites against actual file content. This is what /speckit.audit does that code review cannot: it audits what the convention says should exist, not just what does exist.

**Pattern instance (Claude-Root, 2026-04-18):**
memory-convention.md documented that speckit.plan, speckit.review, and speckit.audit should call memory_recall/memory_store with a constitution gate check. ADR-051 formalized the gate. T018 test passed (checked for constitution keyword, which appeared in skill files for unrelated calibration context). Audit surfaced that the skill files had zero memory calls — the convention was aspirational. Fix: added gate + recall/store to all three skills; tightened T018 to require memory_enabled specifically.

**Cross-project signal:**
Any project with convention documents (memory-convention.md, coding-standards.md, api-patterns.md) faces this risk. Writing the convention is not the same as wiring it into all consumers. The convention should either (a) include a test that verifies a live call site, or (b) be explicitly marked as aspirational until wired.
