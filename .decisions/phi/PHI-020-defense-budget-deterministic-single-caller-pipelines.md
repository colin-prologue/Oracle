<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-020 — Defense Budget in Deterministic Single-Caller Pipelines

**Date:** 2026-05-16
**Domain:** architecture
**Source Project:** Claude-Root
**Source:** ADR-022 receipt protocol elimination (spec 010 autonomous-workflow); pre-push adversarial review identified 70% of helper LOC overrun was defense overhead, not implementation fat.

### Philosophy
In a deterministic system with a single, known caller, prefer static-analysis enforcement over runtime enforcement when the failure mode is an authoring error rather than a runtime race. Adding both is over-design: two defenses for one failure mode in a single-caller deterministic system means one of them is carrying weight it doesn't need to carry.

### Why I Hold This
The ADR-022 receipt protocol (`run-decide-next.sh` + `.run/last-verdict` + `run-emit-event.sh` validation) defended against "LLM bypasses the routing helper at dispatch time." The PR3b-ii static-grep test defends against the exact same class — an authoring error in the slash-command markdown. With one caller and a deterministic routing helper, there is no runtime race; both defenses catch the same failure mode at authoring time. Eliminating the receipt protocol removed 70% of the LOC overrun (783→511 helper LOC) with no reduction in detection coverage. The receipt file also introduced a new failure class: benign Ctrl-C between the two helpers would write a `verdict-omitted` canonical entry, polluting the audit trail it was designed to protect.

### Where It Applies
Any single-caller deterministic pipeline where enforcement choices exist at multiple layers: CI/CD pipeline gates, agent orchestrators, IaC runners (Terraform plan + apply), spec-driven dev workflows, linting harnesses. The question to ask: "Is the failure mode I'm defending against an authoring error or a runtime race?" Authoring errors are caught once at merge/lint time; runtime enforcement adds permanent per-invocation overhead for zero marginal benefit in single-caller systems.

### Known Tensions
Multi-caller systems (shared APIs, concurrent workers, distributed queues) cannot rely on static-analysis enforcement alone — runtime enforcement is load-bearing there because multiple callers introduce race conditions that grep tests cannot catch. The philosophy applies strictly when the caller count is one and the system is deterministic.

### Open to Revision When
A second caller is introduced (the system is no longer single-caller), or when the failure mode shifts from authoring error to runtime race (e.g., external mutation of helper files between authoring and execution). V2 of the orchestrator that introduces concurrent runs or external tool calls would re-evaluate this tradeoff.
