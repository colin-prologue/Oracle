<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-024 — Cross-cutting invariants must hold from the PR they first matter, never deferred to a "hardening" PR

**Date:** 2026-05-19
**Domain:** process
**Source Project:** mini-fax (feature 001-device-firmware plan-gate review finding C-1)
**Source:** Plan-gate /speckit.review identified that LOG-005 scheduled TLS cert pinning in PR 5 (titled "hardening") but PRs 2–4 already performed live HTTPS calls to the Worker. Three plaintext-trusted shippable intermediate states violated Principle IX (NON-NEGOTIABLE outbound-only architecture) hiding inside a defensible-looking PR sequence.

### Philosophy
A constitutional invariant is "non-negotiable" only if it holds from the first PR onward, not the first PR titled "hardening." When you schedule a cross-cutting constraint (auth enforcement, debug-output suppression, cert pinning, audit-log coverage, secret-handling discipline, no-PII-in-logs) to a late PR in a phased delivery, you create shippable intermediate states that violate the constraint. PR-by-PR review tends not to catch this because each local diff looks fine — the violation is in the sequence, not any individual change. Apply this check at task-list time: enumerate every constitutional invariant and verify every PR's scope honors it from PR 1 onward.

### Why I Hold This
The mini-fax cert-pin defect is the cleanest example: PR 2 introduced `WiFiClientSecure` for HMAC-signed polling, PRs 3 and 4 made it a live HTTPS path, and PR 5 was supposed to add the Cloudflare-root-CA pin. Three intermediate states — each "buildable and testable" by the LOG-005 criterion — shipped against the OS root store or with no validation, violating Principle IX while the spec, plan, and amended PR split all passed initial review. The synthesis judge surfaced it only because the PR-split visibility forced the timing to be explicit. A vertical-slice-first approach would have caught it less reliably; a process that doesn't enumerate invariants per PR would have caught it never. The lesson generalizes beyond cert pinning to any constraint labeled "must hold across the feature" but enforced at one point in time.

### Where It Applies
- Security boundaries (TLS pinning, mTLS, signature verification, secret zero-on-free)
- Audit-trail coverage (every action must be logged from PR 1, not "logging hardening" in PR 5)
- Access control (RBAC enforced from first endpoint, not added in a later "auth pass")
- Debug-surface elimination (no Serial.print / no PII in logs / no debug routes — must be RELEASE-build-correct from PR 1)
- License header / compliance markers required across the codebase
- Performance budgets where regression in any PR violates the contract
- Constitutional architecture principles in spec-kit / formal-methods workflows
- Phased feature rollouts where some users see one PR's behavior and others see the next

### Known Tensions
- True "additive" cross-cutting concerns may genuinely belong in a polish PR (e.g., performance optimization that doesn't change correctness, code-comments improvements). The principle applies to invariants — properties whose violation is a defect — not to additive polish.
- Enforcing every invariant from PR 1 inflates PR 1's scope; for a 4-device hobby batch the cost is real. Counter-balance: invariants are typically much smaller than the feature work they constrain (one `setCACertBundle()` call vs hundreds of lines of poll logic).
- Some invariants legitimately depend on infrastructure that arrives mid-feature (you can't enforce mTLS if you don't have certs yet). For these, the dependency itself becomes PR 1's scope.

### Open to Revision When
- The PR sequence ships as a single unit (no shippable intermediate states), making the "intermediate states violate the invariant" critique moot.
- Each invariant has a CI/lint gate that fails the build automatically if any commit violates it, removing reliance on human review-time enforcement.
- The constraint is genuinely additive-only and "violation" is not a defined defect at intermediate stages (rare for true constitutional principles).
