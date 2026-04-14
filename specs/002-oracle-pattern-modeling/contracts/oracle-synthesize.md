# Contract: `/oracle-synthesize` Skill

**Version**: 1.0 | **Date**: 2026-04-13

## Purpose

Synthesize an Observation from retained CDRs/ADRs via a reflect query, present it for curation, and retain the curated result to the oracle bank.

## Invocation

```
/oracle-synthesize
```

No arguments required. The query is fixed (always the pattern synthesis question). May accept an optional argument to override the query for specialized synthesis runs.

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| Daemon URL | Hardcoded `http://localhost:9077` | Yes |
| Bank ID | Hardcoded `oracle` | Yes |
| Reflect budget | Hardcoded `high` (pattern synthesis needs more context than decision queries) | Yes |

## Execution Steps

1. **Reflect query** — POST to `/v1/default/banks/oracle/reflect`:
   ```json
   {
     "query": "What patterns define how I make architecture decisions? Cite specific CDR IDs (e.g., CDR-001) in your response to ground the synthesis.",
     "budget": "high"
   }
   ```

2. **Present for curation** — Show raw reflect output. Ask developer to review and edit.

3. **Extract citations** — Parse the curated text for CDR/ADR ID references (pattern: `CDR-\d{3}` or `ADR-\d{3}`). These populate `metadata.derived_from`.

4. **Confirm retention** — Show final curated text and extracted citations. Ask for explicit confirmation.

5. **Retain as Observation** — POST to `/v1/default/banks/oracle/memories`:
   ```json
   {
     "items": [{
       "content": "<curated text>",
       "context": "observation",
       "document_id": "OBS-NNN",
       "metadata": {
         "type": "observation",
         "project": "hindsight-decision-oracle",
         "date": "<today>",
         "derived_from": ["CDR-001", "CDR-002", ...],
         "query": "What patterns define how I make architecture decisions?"
       }
     }]
   }
   ```

6. **Report** — Confirm OBS-NNN retained. Suggest next step: update Decision Constitution.

## Outputs

| Output | Description |
|--------|-------------|
| Terminal confirmation | "OBS-NNN retained to oracle bank" |
| Implicit | Observation queryable via future reflect and recall operations |

## Error Handling

| Condition | Behavior |
|-----------|----------|
| Daemon not running | Surface start command; do not proceed |
| Reflect returns empty | Report "insufficient data — bank may need more CDRs"; do not retain |
| No CDR citations in reflect output | Warn user; ask whether to proceed with `derived_from: []` |
| Retain fails | Report error; offer to retry or save curated text to clipboard |

## Invariants

- Never auto-retain without explicit developer confirmation
- `derived_from` must have ≥ 2 entries unless the developer explicitly overrides
- `document_id` must be sequential — check existing OBS-* files before assigning
