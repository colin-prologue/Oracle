<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-011 — Verify dependency removal claims against actual artifacts

**Date:** 2026-04-25
**Domain:** process
**Source Project:** Claude-Root
**Source:** Redis audit — user asked whether Redis was still needed after memory server removal; narrative said no, but a codebase scan was required to confirm

### Philosophy
Before accepting a claim that a component, dependency, or convention is no longer needed, verify against actual artifacts rather than reasoning about what should be true.

### Why I Hold This
In this session, the memory server removal led to a plausible narrative that Redis was gone. The correct move was to grep the repo before agreeing. The scan found Redis in two agent instruction files as illustrative examples and in the benchmark fixture — neither stale, but the narrative alone was not sufficient evidence.

### Where It Applies
Any dependency pruning, tech debt removal, or simplification effort. Especially when a major component is removed and the reasoning is "X depended on Y, so Y is gone too."

### Known Tensions
For large codebases, a full scan is expensive. The principle is most load-bearing when the claim is about total absence — "we no longer use X anywhere" — which is hard to verify by reasoning alone.

### Open to Revision When
If the codebase has reliable dependency graphs (lockfiles, import maps, module registries) that can be queried programmatically, manual scanning becomes redundant. Trust the graph, not the narrative.
