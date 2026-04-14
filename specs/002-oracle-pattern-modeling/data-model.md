# Data Model: Oracle Pattern Modeling

**Branch**: `002-oracle-pattern-modeling` | **Date**: 2026-04-13

## Entities

### Observation

A synthesized pattern statement produced by a `reflect` query, reviewed and curated by the developer before retention.

| Field | Type | Description |
|-------|------|-------------|
| `content` | string | Curated pattern text (markdown). May be edited from raw reflect output. |
| `context` | string | `"observation"` — distinguishes from CDRs/ADRs in recall |
| `document_id` | string | e.g., `OBS-001` — short identifier for cross-referencing |
| `metadata.type` | string | `"observation"` |
| `metadata.project` | string | `"hindsight-decision-oracle"` |
| `metadata.date` | string | ISO 8601 date of curation |
| `metadata.derived_from` | list[string] | CDR/ADR IDs cited in the synthesis (e.g., `["CDR-001", "CDR-003", "CDR-005"]`) |
| `metadata.query` | string | The reflect query that produced this Observation |

**Retention endpoint**: `POST /v1/default/banks/oracle/memories`

**Validation rules**:
- `derived_from` MUST contain at least 2 entries (FR-002)
- `content` must be reviewed before retention — never auto-retained from raw reflect output
- `document_id` must be sequential (OBS-001, OBS-002, …)

**State transitions**: Draft (reflect output) → Curated (developer-edited) → Retained (in oracle bank)

---

### Decision Constitution (Mental Model)

The oracle's living document describing Colin's architectural preferences and non-negotiables. Stored in Hindsight as a Mental Model.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | `"Decision Constitution"` — stable identifier |
| `description` | string | Full constitution text (markdown). Updated after each Observation cycle. |

**Retention endpoint**: `POST /v1/default/banks/oracle/mental_models`

**Validation rules**:
- Updates must reference at least one Observation-derived pattern that was not in the previous version (SC-002)
- The `name` field must remain `"Decision Constitution"` for stable recall

**File on disk**: `.claude/.decisions/DECISION_CONSTITUTION.md` (kept in sync with Mental Model)

---

### Cadence Query

A reusable, documented reflect invocation for periodic drift detection. Not a retained entity — a documented string.

| Field | Type | Description |
|-------|------|-------------|
| Query 1 | string | `"Summarize the current synthesized Observations in the oracle bank."` |
| Query 2 | string | `"Compare these Observations against the most recently retained CDRs. Flag any pattern shifts or contradictions."` |

**Execution**: Two sequential `/oracle` calls. Run at the start or end of any working session after adding CDRs.

**No daemon configuration required** — runs against the standard oracle bank with existing reflect budget settings.

---

## Entity Relationships

```
CDRs (CDR-001..CDR-005) ──→ reflect ──→ draft Observation
                                              │
                                         [curate]
                                              │
                                              ▼
                                    Observation (OBS-001)
                                              │
                                         [review]
                                              │
                                              ▼
                                 Decision Constitution (updated)
                                              │
                                    [cadence query compares]
                                              │
                                              ▼
                              future CDRs checked for drift
```
