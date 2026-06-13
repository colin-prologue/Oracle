<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

Two patterns that complement OBS-001's constraint-aware workflow but weren't explicitly named there.

**Pattern 8 — Validate via Structured Evidence Before Committing**
High-confidence decisions require multiple independent confirmation points, not intuition. Root causes are confirmed by reading source code; cascades are reproduced before a fix is committed. If you can't cite a concrete confirmation point, lower your stated confidence.
- CDR-001: "root cause confirmed by reading claude_code_llm.py; cascade reproduced twice before fix identified"
- CDR-005: "verified via launchctl list showing PID, daemon health check passing, and source code inspection"
- CDR-006: "root cause directly observed; fix is minimal and reversible"

**Pattern 9 — Quality Over Completeness in Signal/Noise Tradeoffs**
When designing capture or retention systems, prefer fewer high-quality signals over comprehensive-but-noisy ones. A missed chat exchange is acceptable; a missed CDR is not. This drove: disabling autoRetain, retaining only on SessionEnd/PreCompact/explicit invocation, and running /oracle-synthesize periodically rather than continuously.
- CDR-006 (selective retention over crash resilience)
- CDR-007 (two-skill split preserves reflect query clarity)

**Meta-theme:** Both patterns reflect the same discipline applied at different levels — deliberate signal selection over automatic accumulation, whether accumulating evidence for a decision or accumulating memories in the oracle bank.
