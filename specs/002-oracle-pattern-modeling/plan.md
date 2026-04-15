# Implementation Plan: Oracle Pattern Modeling

**Branch**: `002-oracle-pattern-modeling` | **Date**: 2026-04-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-oracle-pattern-modeling/spec.md`

## Summary

Phase 3 of the Decision Oracle: synthesize an Observation from 5 retained CDRs + 1 ADR, curate it before retaining, update the Decision Constitution Mental Model in Hindsight, and define a repeatable cadence query for drift detection. This is primarily a workflow and tooling feature — the core deliverable is a new `/oracle-synthesize` skill and documented cadence query, not new infrastructure.

## Technical Context

**Language/Version**: Python 3.14 (scripts) — no new runtime  
**Primary Dependencies**: Hindsight daemon (http://localhost:9077), hindsight-embed (uvx), Anthropic API (claude-haiku-3)  
**Storage**: Hindsight oracle bank (postgresql via daemon) + `.decisions/` markdown files  
**Testing**: Manual acceptance testing against running daemon  
**Target Platform**: macOS (LaunchAgent-managed daemon)  
**Project Type**: CLI skill + documentation  
**Performance Goals**: Reflect response within 30s (SC-003)  
**Constraints**: Daemon must be running; haiku TPM limit — avoid concurrent retain+reflect (CDR-004)  
**Scale/Scope**: Single developer, 5 CDRs + 1 ADR in bank

## Constitution Check

*Constitution template is unpopulated for this project — no gates defined. No violations to check.*

## Project Structure

### Documentation (this feature)

```text
specs/002-oracle-pattern-modeling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output (cadence query reference)
└── contracts/
    └── oracle-synthesize.md   # Skill interface contract
```

### Source Code

```text
.claude/skills/
└── oracle-synthesize/
    └── SKILL.md          ← new skill for Observation synthesis + curation

.decisions/
├── cdrs/                 ← no new files (CDR-001 through CDR-005 already exist)
└── adrs/                 ← no new files

.claude/.decisions/
└── DECISION_ORACLE.md    ← Phase 3 roadmap items → checked off
```

**Structure Decision**: No new source directories. The oracle skill infrastructure is already in `.claude/skills/`. Phase 3 adds one skill and documentation only.

## Complexity Tracking

> No constitution violations.
