<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-009 — Write to the durable store first; the other copy is a derivative

**Date:** 2026-04-25
**Domain:** architecture
**Source Project:** hindsight
**Source:** Centralizing PHI files revealed a write-ordering bug: oracle-preclear was writing the file before retaining to the oracle bank. An auto-compact mid-run could orphan the file (in the wrong repo, no less) without the bank ever knowing. Reordering — bank first, file second — made interruptions safe: the worst failure mode loses a regenerable cache copy, not the canonical record.

### Philosophy
When writing the same datum to two stores with asymmetric durability or recovery semantics (e.g., a transactional database vs. a filesystem copy), retain to the more durable store first and treat the other as a derivative. A mid-process interruption can then only orphan the recoverable copy, never the canonical record. The order of writes encodes which store is the source of truth.

### Why I Hold This
The default instinct is "do the cheap, fast write first" — usually a local file. That feels safe because the local write is unlikely to fail. But "unlikely" hides what happens when the *next* step fails: now the durable store doesn't know about the data, and the local file is the only record — exactly inverted from the intended source-of-truth relationship. Reversing the order makes the failure mode benign: an interrupted derivative write means a recoverable cache miss, not a lost record.

### Where It Applies
- Memory bank + filesystem cache (this case)
- Database transaction + log file (commit DB first, log second; if the log write fails the DB still has the truth)
- Cloud upload + local artifact (upload first, then move local copy to "uploaded" folder)
- Event publish + local audit trail (publish event first; the trail is for humans, not consumers)
- Migration + rollback file (apply migration, then write rollback metadata; if rollback metadata fails you still know what happened)

The pattern: identify the asymmetry, then write so that crashing in the middle leaves the durable store consistent and the derivative recoverable.

### Known Tensions
- "Durable" depends on context. A local SQLite database may be more durable than an unreliable network store. The principle is about *relative* durability and *recoverability of the derivative*, not absolute storage choices.
- Some derivatives can't be regenerated cheaply (e.g., a UI screenshot). In that case the asymmetry weakens — both stores are partially canonical, and you need a different consistency strategy (transactions, two-phase commit, idempotent retry).
- For cheap idempotent operations the order may not matter; this principle is most load-bearing when interruptions are realistic and recovery is asymmetric.

### Open to Revision When
- The two stores are joined by a transaction or a coordinator that guarantees atomicity (e.g., distributed transactions, write-ahead logs that span both). At that point ordering is irrelevant — the system enforces consistency.
- The "derivative" is no longer regenerable, which means it's actually canonical too and the asymmetry was misjudged. Reclassify before applying this principle.
