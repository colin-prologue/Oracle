<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

## OBS-006 — Category-error bugs come in clusters; inventory before declaring done

**Date:** 2026-04-25
**Derived from:** PHI-008 (cross-project artifacts in owning repo); PHI-002 write-durable-first corollary (ex-PHI-009 — merged 2026-07-06)
**Relationship:** extended by OBS-020 (same bug-clustering principle, second project — graduation candidate pair)

### Pattern
When investigating a category-error bug, scan for cousins of the same shape before declaring the fix complete. The PHI-leakage bug surfaced one stray file in Travel, but the audit revealed three more divergences: PHI-007 retained to the bank with no corresponding file, PHI-001/002/003 on disk but missing from the bank, and 7 session-log records polluting reflect output. Each shared the same root cause (loose store-to-store coupling) but only one was visible until an explicit inventory was run. Pattern: one bug of category X is evidence that more X-shaped bugs exist; allocate a few minutes to look before assuming the first fix was the only fix.

### Why this happens
Category-error bugs aren't usually caused by one bad line of code — they're caused by a missing constraint that the whole system was tacitly violating. Once one violation is found and fixed, the natural assumption is "we fixed it." But the missing constraint is still missing everywhere else; the only thing that changed is now you know to look. The first instance is the loudest, not the only one.

### Where this applies
- Schema drift: one stale column in one query → audit the others
- Auth bypass: one missing check on one endpoint → grep for the pattern
- Off-by-one in loop bounds: one occurrence → other places using the same iteration idiom
- Inconsistent state stores (this case): one orphaned file → full state reconciliation
- Unicode handling: one mojibake report → audit every encode/decode boundary

### Practical rule
After fixing a category-error bug, spend a small fixed budget (10 min, or one targeted grep + read pass) looking for cousins. If the budget is exceeded with no findings, stop and ship the fix; the population is bounded. If multiple cousins surface quickly, the inventory just paid for itself many times over and is worth continuing.

### Known tension
For genuine one-off bugs (a typo, a single overlooked branch), the cousin scan is wasted effort. But the cost of a 10-minute scan is far below the cost of shipping with N more instances of the same bug live; the asymmetry favors the scan even when most scans come up empty.
