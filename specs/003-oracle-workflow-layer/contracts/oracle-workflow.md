# Contract: Oracle Workflow Layer

## Native Query Workflow

### Input

- `question`: non-empty decision question.
- `source`: caller marker, such as `native`, `claude-skill`, `codex-mcp`, or `compat-shim`.
- `bank`: Hindsight bank, expected to be `oracle` unless a later migration note approves another namespace.

### Required Behavior

1. Query Hindsight recall for candidate PHI/OBS material.
2. Apply the strict relevance gate.
3. If no candidates are genuinely relevant, return exactly:

   ```text
   The oracle has no entries relevant to that question.
   ```

4. If relevant candidates exist, synthesize a concise answer that:
   - cites PHI/OBS identifiers when available;
   - marks missing identifiers explicitly when a relevant memory lacks one;
   - surfaces tensions or counter-evidence before recommendation;
   - separates cited Oracle memory from current-session inference.
5. Write one canonical audit entry for the attempt when logging is possible.

### Audit Contract

Audit entries must include:

- `timestamp`
- `client` or `workflow_source`
- `question`
- `recall_substrate`
- `retrieved_ids`
- `accepted_ids`
- `rejected_ids`
- `rejection_reasons`
- `result_count`
- `outcome`
- `error`, when applicable

Rejected candidate full text is omitted by default. Verbose rejected-candidate content requires explicit diagnostic mode or later approved capture.

### Failure Behavior

- Recall failure: return an actionable unavailable/error message and log a failure entry when possible.
- Logging failure after successful recall: surface the audit failure; do not claim the attempt is fully auditable.
- Empty recall and irrelevant recall: treat as valid empty-result misses, not system failures.

## Capture Workflow

### Input

- `candidate_type`: `PHI` or `OBS`.
- `draft_text`: proposed durable entry.
- `metadata`: date, source, domain, derived-from IDs, source project where applicable.
- `approval`: explicit user approval.

### Required Behavior

1. Draft candidate from session context or user-provided material.
2. Present candidate for approval, edit, reject, or defer.
3. Do not retain or write canonical markdown before explicit approval.
4. After approval, retain to Hindsight first.
5. After retain succeeds, write or regenerate the canonical markdown mirror.
6. If markdown persistence fails after retain, report partial success and provide duplicate-safe retry/regeneration.
7. If retain fails, do not create canonical markdown for that unretained entry.

## Pre-Clear Workflow

### Required Behavior

1. Before context loss/session clear, extract 0-3 high-signal capture candidates.
2. Present candidate type, rationale, related IDs, and source context.
3. If no candidate meets the bar, report that no capture candidates were found.
4. Reuse the Capture Workflow for approved candidates.
5. Do not retain unapproved candidates.

## Compatibility Query Workflow

### Required Behavior

1. Delegate to the Native Query Workflow.
2. Preserve Oracle semantics for all supported legacy paths.
3. Preserve exact legacy response shape only when the migration matrix names an active consumer requiring it.
4. Write the same canonical audit entry as native calls, with a compatibility source marker.
5. Emit or document migration notes for paths whose shape changes.
