## PHI-003 — Prefer conscious capture over automatic retention

**Date:** 2026-04-14
**Domain:** tooling, oracle-design
**Source:** CDR-006 — oracle bank retain strategy: explicit capture only

### Philosophy
Only retain what you consciously choose to retain. Automatic, high-frequency retention optimizes for completeness but degrades signal quality — the bank fills with noise faster than reflection can surface patterns.

### Why I Hold This
With autoRetain enabled, the oracle bank accumulated 516 nodes and 76 auto-observations from ordinary conversation content rather than decisions. Reflect quality degraded because the signal was buried in noise. The Haiku rate limit was saturated continuously, blocking the reflect queries the bank was built to serve. Explicit capture — SessionEnd summaries, PreCompact hooks, deliberate `/oracle-debate` invocations — produces a smaller, higher-quality bank where every entry earned its place.

### Where It Applies
Any memory or knowledge system where retrieval quality matters more than completeness: decision oracles, knowledge bases, note systems, vector stores. The instinct to capture everything is strong but counterproductive when the retrieval mechanism depends on signal density.

### Known Tensions
Explicit capture creates a coverage gap: insights that aren't captured at session end are lost. AutoRetain's value is crash resilience and continuity. The tradeoff is real — this philosophy accepts coverage loss in exchange for reflect quality.

### Open to Revision When
Retrieval systems can reliably filter signal from noise at query time (rather than requiring it at write time), or rate limits increase enough that continuous retention no longer contends with reflection.
