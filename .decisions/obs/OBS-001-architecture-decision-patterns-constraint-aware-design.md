<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

## OBS-001 — Architecture Decision Patterns: Constraint-Aware Design

**Date:** 2026-04-14
**Derived from:** CDR-001, CDR-002, CDR-003, ADR-001
**Query:** What patterns define how I make architecture decisions?

---

### Pattern 1: Prioritize Stateless, Independent System Design
*(CDR-001, CDR-003)*

Reject session-bound or stateful models in favor of decoupled, independently-operable architectures — even when the stateless option adds complexity elsewhere. CDR-001 shows this directly: claude-code was preferred for credential consolidation but rejected because it is session-bound; anthropic was chosen despite requiring an extra key because the daemon must operate independently. CDR-003 shows the same instinct applied to configuration: explicit, discoverable paths over magic loading order that fails silently.

**Recurring preference:** Architecture constraints trump convenience. When a preferred option violates a hard requirement (session independence, discoverability), the preferred option loses.

---

### Pattern 2: Surface Constraints, Not Just Outcomes

Decisions are only fully documented when the constraint that ruled out alternatives is visible. CDR-002 does not just record "set the CPU flags" — it records that MPS is incompatible with Python 3.14 multiprocessing on Apple Silicon, and that the flags must persist in the profile regardless of how the daemon is launched. The constraint is the revisit trigger: if the platform constraint changes, the decision changes with it.

**Recurring preference:** A decision without its constraint is an orphan. Future-self needs to know what would have to change to make the rejected option viable.

---

### Pattern 3: Distinguish Pressure-Driven from Deliberate Design

Categorize decisions by whether they were made under time or resource pressure versus deliberate architectural reasoning. Pressure-driven decisions are candidates for revisiting when pressure relaxes; deliberate decisions should stay until a constraint changes. This distinction is why the oracle is configured to model shipping velocity vs. technical debt tradeoffs — capturing when velocity drove a decision, not just what was decided.

**Recurring preference:** Do not let pressure-driven choices calcify into architectural norms.

---

### Pattern 4: Build Only What the Task Requires

Resist the impulse to generalize before a second concrete use case exists. This is not a project-specific rule but a default posture: a one-time operation does not need a wrapper, a single use case does not need configurability, and three similar lines of code are better than a premature abstraction. When the instinct to abstract appears, the question is "what is the second use case?" — if the answer is hypothetical, the abstraction does not ship.

**Recurring preference:** Complexity is a liability that must be justified by concrete, present requirements — not anticipated future ones.

---

### Pattern 5: Default to Self-Contained, Locally-Operated Tooling

Prefer tools that run without external service dependencies over those that require accounts, cloud APIs, or network availability — especially in a solo-developer context where operational overhead compounds directly into friction. CDR-001 reflects this: the initial preference was to avoid an extra API key by using a locally-available provider. The preference was overridden by an architecture constraint, but the instinct was sound and consistent. When two options are otherwise equivalent, the one with fewer external dependencies wins.

**Recurring preference:** Minimize the number of external systems that must be operational for local development to work.

---

### Meta-Pattern: Constraint-Aware Decision-Making

Across all CDRs: identify the hard constraints first, explore options within them, document the choice and the constraint that ruled out alternatives, mark which constraints are permanent vs. revisitable, and validate assumptions through structured retrospectives when circumstances change.

This is why the Decision Oracle exists: to surface these constraints automatically so future decisions do not re-traverse solved ground.
