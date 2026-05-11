# Research: Decision Oracle Workflow Layer Migration

## Decision: Make `scripts/mcp_server.py` / base Hindsight workflow the primary Oracle path

**Rationale**: The feature goal is to remove duplicated Oracle-specific runtime behavior while preserving user-facing Oracle semantics. The repo already has `scripts/mcp_server.py` exposing Hindsight primitives and an `hindsight_oracle_query` helper that returns the relevance-gate envelope. Building the workflow layer around this primary adapter avoids a second memory system and avoids keeping `mcp/oracle-query/server.py` as a parallel implementation.

**Oracle support**: PHI-007 favors extracting a shared spec rather than forcing one implementation to subsume another. The uniform audit-trail principle favors folding exceptions into the main path so future readers and tools understand one audit shape.

**Alternatives considered**:

- Keep standalone `mcp/oracle-query` as the primary path. Rejected because it preserves duplicated runtime logic and creates divergent audit behavior.
- Build a new Oracle-specific service over Hindsight. Rejected because the spec explicitly forbids a second memory system and duplicated server behavior.

## Decision: Preserve Oracle semantics in workflow instructions, not in a separate memory substrate

**Rationale**: Oracle value comes from rituals and semantics: recall before decisions, strict relevance gate, exact empty signal, citations, tensions-first synthesis, deliberate capture, pre-clear candidate extraction, and auditability. These can be expressed as skills, commands, hooks, contracts, and tests over Hindsight recall/retain/query logging.

**Oracle support**: PHI-005 supports automating extraction rather than execution. PHI-003 supports explicit user approval for durable capture.

**Alternatives considered**:

- Encode Oracle as a separate daemon or standalone bank API. Rejected as duplicated runtime/server behavior.
- Retain every query/candidate automatically. Rejected because it violates conscious capture and degrades signal quality.

## Decision: Use a single canonical audit record shape with source markers

**Rationale**: Native workflow calls, empty-result misses, failures, and compatibility-shim calls should all write the same audit fields where possible. Source markers distinguish `native`, `compat-shim`, or client-specific origins without changing the record shape.

**Oracle support**: The uniform audit-trail principle directly applies: multiple decision paths with multiple audit shapes create future debugging and test burden.

**Alternatives considered**:

- Preserve old audit shapes per caller. Rejected because it keeps the duplicated audit problem the migration is meant to remove.
- Only log aggregate counters. Rejected because the user needs query-level auditability to judge bank usefulness and coverage gaps.

## Decision: Log full query text but not full rejected candidate bodies by default

**Rationale**: Full query text is necessary to evaluate misses and coverage gaps. Full rejected candidate bodies can turn the audit log into a shadow memory bank and may retain sensitive/project-local content accidentally. Store identifiers, outcomes, and rejection reasons by default; allow verbose diagnostics only through explicit diagnostic mode or approved capture.

**Alternatives considered**:

- Log full rejected candidate text every time. Rejected as excessive durable capture.
- Redact all query text. Rejected because it makes audit review too weak to judge bank usefulness.

## Decision: Preserve bank-first capture ordering

**Rationale**: Hindsight bank retention is the operational memory write. Canonical markdown is the human-reviewable repo mirror. Capturing to the bank first means context loss can only lose a regenerable mirror, not the memory entry itself. If markdown writing fails, retry/regenerate from the retained entry without duplicate retain.

**Oracle support**: Prior Oracle memory records a concrete `oracle-preclear` write-ordering bug where file-first behavior orphaned files without bank knowledge. PHI-002 supports durable writes being owned by durable processes.

**Alternatives considered**:

- File-first capture. Rejected because it recreates the previous orphan-file failure mode.
- Two-phase all-or-nothing capture. Rejected because current Hindsight/file primitives do not provide a real transaction boundary and would add complexity outside the scope.

## Decision: Require Hindsight-root path anchoring for canonical files and query logs

**Rationale**: Canonical PHI/OBS markdown and query logs belong to the Hindsight repository, even when Oracle workflows are invoked from consumer projects. Path resolution must use `HINDSIGHT_ROOT` or the repository fallback, never `cwd`.

**Oracle support**: PHI-008 records a concrete bug caused by writing Oracle artifacts through current working directory resolution into a consumer project.

**Alternatives considered**:

- Use the caller's working directory. Rejected because it recreates known cross-project leakage.
- Require a user-provided path per invocation. Rejected because it increases capture friction and risks inconsistent roots.

## Decision: Use consumer-based compatibility

**Rationale**: All legacy Oracle paths must preserve Oracle semantics. Exact old response shape is required only when the migration matrix names an active consumer that depends on it. This keeps known dependents working while avoiding duplicate response-shape maintenance for unused paths.

**Alternatives considered**:

- Exact compatibility for every legacy path. Rejected because it retains too much duplicated compatibility surface.
- Semantic-only compatibility for all paths. Rejected because it could break a real consumer that has not yet been inventoried.

## Decision: Deprecate standalone `oracle-query` only after tests, explicit approval, and one clean dogfood session

**Rationale**: Acceptance tests validate intended behavior, but manual use finds assumption drift that tests and reviews can miss. Removal should wait for passing tests, explicit user approval, and one manual dogfood session with no blocking regressions.

**Oracle support**: PHI-016 requires manual-use assumption checks before follow-on work removes or builds on prior behavior.

**Alternatives considered**:

- Remove after tests only. Rejected because it ignores manual-use assumption drift.
- Keep indefinitely. Rejected because it leaves duplicated runtime logic in place.
