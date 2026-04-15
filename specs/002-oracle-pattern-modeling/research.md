# Research: Oracle Pattern Modeling

**Branch**: `002-oracle-pattern-modeling` | **Date**: 2026-04-13

---

## 1. Hindsight Observation Network — Auto vs. Manual

**Question**: Are Observations in Hindsight auto-synthesized or can they be manually retained? Can the developer curate before retaining?

**Finding**: Hindsight's Observation network is described as "auto-synthesized patterns" in the architecture docs. However, the `retain` API accepts a `context` field on any memory — the Observation network concept is a Hindsight LLM abstraction over retained memories, not a separate storage tier with a different endpoint. The developer can:
1. Run a `reflect` query to get synthesized output
2. Treat the output as a draft Observation
3. Edit it
4. Manually retain it to the oracle bank with `context: 'observation'` metadata

**Decision**: Manual retain after curation is the right approach. Hindsight's auto-synthesis may run asynchronously on the Observation network — but for explicit, curated Observations (the primary artifact of Phase 3), we use the `POST /v1/default/banks/oracle/memories` endpoint with `context: 'observation'`.

**Rationale**: FR-003 requires the developer be able to edit the synthesized text before retaining. Auto-synthesis bypasses this. Manual retain with reviewed content ensures Observation quality.

**Alternatives considered**: Rely entirely on auto-synthesis (Hindsight's Observation layer). Rejected: no curation step; quality depends entirely on LLM; inconsistent with the oracle's "semi-manual by design" CDR philosophy.

---

## 2. Hindsight Mental Model API — Create vs. Update

**Question**: How do you update an existing Mental Model (Decision Constitution) in Hindsight? Is there a PATCH endpoint or does create upsert by name?

**Finding**: From DECISION_ORACLE.md setup, `client.create_mental_model(bank_id, name, description)` is the API call shown. The REST endpoint inferred is `POST /v1/default/banks/{bank_id}/mental_models`. Hindsight's typical pattern is upsert-by-name — creating a Mental Model with the same name as an existing one overwrites or versions it.

**Workaround for uncertainty**: Since the daemon is not running for verification, the skill will use `POST /v1/default/banks/oracle/mental_models` with the full updated description. If the endpoint returns a conflict error, we fallback to `PUT` or `PATCH` with the model ID. The skill documents both paths.

**Decision**: Use `POST /v1/default/banks/oracle/mental_models` with the full updated content. Treat as upsert. If that fails, retrieve the existing model's ID and use `PUT /v1/default/banks/oracle/mental_models/{id}`.

**Rationale**: Consistent with how the initial constitution was created in Phase 1 setup.

**Alternatives considered**: File-only update (update `.claude/.decisions/DECISION_ORACLE.md` but not the Hindsight Mental Model). Rejected: FR-004 explicitly requires the constitution be updatable as a Mental Model in the bank, not only as a file on disk.

---

## 3. Reflect Output — CDR Citation Structure

**Question**: Does Hindsight's reflect API automatically include CDR identifiers in its output, or does the LLM need to be prompted to include them?

**Finding**: The reflect response has a single `text` field. The LLM composing the response synthesizes from retrieved memories, including metadata. CDR IDs are embedded in the retained content (`## CDR-001 — ...`). When the reflect query asks to "cite specific CDRs," the LLM can reference them from the retained content it retrieves.

**Decision**: The reflect query must explicitly ask for citations: "what patterns define how I make architecture decisions? Cite specific CDR IDs in your response." This ensures FR-002 compliance without changes to the oracle bank or daemon config.

**Rationale**: The LLM will see CDR content in its retrieved context — asking it to cite them is sufficient instruction. No structural changes needed.

**Alternatives considered**: Add citation instructions to the bank's reflect_mission (permanent). Rejected: too broad; not every reflect query needs citations. Keep citation requirement in the query itself.

---

## 4. Cadence Query — Comparability Against Recent CDRs

**Question**: How should the cadence query be structured so its output is "comparable against recent CDRs" (FR-006) without manual cross-referencing?

**Finding**: The key insight is that the cadence query should ask the oracle to compare the existing Observation(s) against recent decisions explicitly. The query can include an instruction like: "Compare the current Observation [ID or summary] against the most recent CDRs. Flag any patterns that have shifted." This produces a structured comparison rather than a generic synthesis.

**Decision**: The cadence query is a two-part reflect:
1. `"Summarize the current synthesized Observations in the oracle bank."`
2. `"Compare these Observations against the most recently retained CDRs. Flag any pattern shifts or contradictions."`

These can be two separate `/oracle` calls in sequence. The second call's output is directly comparable to recent CDRs since it references them explicitly.

**Rationale**: A single query asking both questions risks the LLM blending them. Two sequential calls produce cleaner, independently reviewable output.

**Alternatives considered**: Structured JSON response format for cadence query. Rejected: adds schema dependency to the reflect API that may not be supported; markdown output is sufficient for developer review.

---

## 5. Skill Gap — Missing Curation Workflow

**Finding**: The existing `/oracle` skill runs a reflect query and presents results. The existing `/oracle-capture` skill captures CDRs. Neither skill handles the Observation curation workflow:
- Present reflect output
- Allow editing
- Retain with `context: 'observation'` and CDR citations preserved

**Decision**: Create a new `/oracle-synthesize` skill that covers the full synthesis-curation-retain loop for Observations.

**Alternatives considered**: Extend `/oracle` to support an `--synthesize` flag. Rejected: conflates two distinct operations — querying the oracle for a decision vs. synthesizing the oracle's own pattern model. Keeping them as separate skills is cleaner and consistent with the existing skill naming pattern.

---

## Summary

| Unknown | Resolution |
|---------|-----------|
| Observation network: auto vs. manual | Manual retain via `POST /memories` with `context: 'observation'` |
| Mental Model update API | `POST /mental_models` (upsert-by-name); fallback to PUT with ID |
| CDR citations in reflect output | Include explicit citation instruction in query text |
| Cadence query comparability | Two sequential reflect calls (summary + comparison) |
| Missing curation workflow | New `/oracle-synthesize` skill |
