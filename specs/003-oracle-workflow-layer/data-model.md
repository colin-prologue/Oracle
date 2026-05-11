# Data Model: Decision Oracle Workflow Layer Migration

## OracleWorkflowLayer

Represents the instructions, skills, commands, hooks, and compatibility adapters that implement Oracle semantics over base Hindsight primitives.

**Fields**:

- `name`: stable workflow name, such as `oracle-query`, `oracle-capture`, or `oracle-preclear`.
- `source`: invocation source, such as `native`, `compat-shim`, `claude-skill`, `codex-mcp`, or `hook`.
- `uses_hindsight_recall`: boolean.
- `uses_hindsight_retain`: boolean.
- `uses_query_logging`: boolean.
- `preserves_oracle_semantics`: boolean.

**Validation rules**:

- Must not introduce a second memory substrate.
- Must use the canonical relevance gate when answering decision questions.
- Must write audit entries through the canonical audit shape when query attempts occur.

## HindsightRecallResult

Candidate prior memory returned by Hindsight recall for relevance-gate evaluation.

**Fields**:

- `text`: recalled memory text.
- `type`: memory type from Hindsight.
- `document_id`: optional PHI/OBS identifier.
- `mentioned_at`: optional timestamp.
- `metadata`: optional structured metadata.

**Validation rules**:

- `text` and `type` are required for synthesis.
- `document_id` should be used for citations when present.
- If no identifier is available but the memory is relevant, synthesis must mark the citation gap explicitly.

## RelevanceGateResult

Decision record for whether recalled memories are genuinely relevant.

**Fields**:

- `query`: user or agent decision question.
- `retrieved_ids`: identifiers available from recalled candidates.
- `accepted_ids`: identifiers judged genuinely relevant.
- `rejected_ids`: identifiers rejected by the relevance gate.
- `rejection_reasons`: short reasons for rejected candidates.
- `outcome`: one of `relevant`, `empty`, `irrelevant`, or `failure`.

**State transitions**:

```text
retrieved candidates
  -> relevant      when one or more candidates are genuinely relevant
  -> irrelevant    when candidates exist but none pass the gate
  -> empty         when Hindsight returns no candidates
  -> failure       when recall cannot complete
```

**Validation rules**:

- `irrelevant` and `empty` Oracle answers must return exactly `The oracle has no entries relevant to that question.`
- `rejected_ids` may be logged by identifier and reason, but rejected candidate bodies are not logged by default.

## OracleQueryAuditEntry

Uniform durable audit record for Oracle query attempts.

**Fields**:

- `timestamp`: query attempt time.
- `client`: calling client or workflow source.
- `question`: full query text.
- `workflow_source`: native workflow, compatibility shim, skill, hook, or MCP client marker.
- `recall_substrate`: Hindsight bank/recall path used.
- `retrieved_ids`: candidate identifiers when available.
- `accepted_ids`: identifiers accepted by the relevance gate.
- `rejected_ids`: identifiers rejected by the relevance gate.
- `rejection_reasons`: concise reasons for gate rejection.
- `result_count`: number of recalled candidates.
- `outcome`: `relevant`, `empty`, `irrelevant`, or `failure`.
- `error`: error detail when recall or logging fails.

**Validation rules**:

- Native and compatibility-shim calls use the same shape.
- Empty-result misses are first-class outcomes, not errors.
- Rejected candidate full text is omitted by default.

## CaptureCandidate

Pre-retention PHI/OBS proposal extracted from session context.

**Fields**:

- `candidate_type`: `PHI` or `OBS`.
- `draft_text`: proposed durable entry text.
- `source_context`: short source summary or snippet.
- `rationale`: why it may be durable.
- `related_ids`: related PHI/OBS identifiers.
- `status`: `proposed`, `approved`, `rejected`, or `deferred`.

**Validation rules**:

- Candidate extraction may be automated.
- Durable retain and markdown writes require explicit approval.
- Unapproved candidates must not be retained as canonical Oracle entries.

## CanonicalOracleEntry

Durable PHI or OBS entry after user approval.

**Fields**:

- `document_id`: `PHI-NNN` or `OBS-NNN`.
- `entry_type`: `philosophy` or `observation`.
- `content`: approved entry body.
- `metadata`: date, source, domain, derived-from, and source project where applicable.
- `bank_status`: `not-retained`, `retained`, or `retain-failed`.
- `markdown_status`: `not-written`, `written`, or `write-failed`.

**State transitions**:

```text
approved
  -> retaining
  -> retained
  -> markdown-writing
  -> complete

approved
  -> retain-failed

retained
  -> markdown-write-failed
  -> retry/regenerate markdown
  -> complete
```

**Validation rules**:

- Hindsight retain must precede canonical markdown write.
- If retain fails, do not create a canonical markdown file.
- If markdown write fails after retain, retry/regenerate without duplicating the retained bank entry.
- Markdown paths must be anchored to `HINDSIGHT_ROOT` or the Hindsight repository fallback, never caller `cwd`.

## CompatibilityShim

Adapter for a legacy Oracle path during migration.

**Fields**:

- `legacy_path`: command, hook, skill, or MCP entrypoint.
- `replacement_workflow`: native workflow it delegates to.
- `status`: `delegated`, `replaced`, `retired`, or `blocked`.
- `active_consumer`: optional named consumer requiring exact legacy response shape.
- `requires_exact_response_shape`: boolean.
- `audit_source_marker`: marker written into audit records.
- `removal_criteria_status`: pass/fail summary.

**Validation rules**:

- Must preserve Oracle semantics while supported.
- Must preserve exact old response shape only when the migration matrix names an active consumer requiring it.
- Must write the same audit record shape as native workflows, plus a source marker.

## MigrationMatrixEntry

Inventory row for each legacy Oracle workflow, command, hook, skill, or MCP path.

**Fields**:

- `legacy_path`: path/name of the legacy surface.
- `owner`: owning area, such as skill, hook, MCP server, script, or docs.
- `current_behavior`: summary of current user-visible behavior.
- `replacement_behavior`: target workflow behavior.
- `status`: `delegated`, `replaced`, `retired`, or `blocked`.
- `active_consumers`: named consumers, if any.
- `exact_shape_required`: boolean.
- `acceptance_tests`: tests required before removal.
- `migration_notes`: documentation/update requirements.
- `rollback_notes`: rollback or restoration instructions.

**Validation rules**:

- Every documented legacy Oracle path must have a matrix entry.
- Standalone `oracle-query` removal is blocked until tests pass, explicit user approval is recorded, and one manual dogfood session has no blocking regressions.
