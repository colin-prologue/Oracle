<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-017 — Vendor-Policy Preconditions in Review Gates

**Date:** 2026-04-30
**Domain:** process
**Source Project:** TravelPlanner
**Source:** Post-merge attempt to satisfy 015-coverage-ci-gate FR-014(c) returned HTTP 403 from both classic branch-protection and rulesets APIs: branch protection on private repos requires a paid GitHub plan. Spec, plan, three review gates, and audit all passed without surfacing this precondition. Captured as LOG-046 (branch_protection_deferred_free_tier_private) and named as a process improvement in the post-015 retrospective.

### Philosophy
Review panels are calibrated to catch architectural and security drift; they do not naturally probe vendor-policy preconditions. When a feature's definition-of-done includes a manual UI step in a third-party platform — branch protection, env-var setup, billing toggle, marketplace install — the review panel should explicitly assert that the step is available on the project's plan posture, not merely documented.

### Why I Hold This
A documented manual step that turns out to be paywalled, region-restricted, or feature-flagged at execution time is a silent class of deferral the panels miss by default. Architectural reviewers ask "is this design sound?", security reviewers ask "is this safe?", devil's advocates ask "what could go wrong?" — none of these naturally lead to "is this purchasable on the plan we are on?". The check is cheap (one explicit assertion per third-party manual step) and prevents a class of failure that only surfaces post-merge.

### Where It Applies
Any feature whose acceptance criteria depend on a third-party platform action that is gated by plan tier, region, beta-program enrollment, or feature-flag rollout. Strongest fit: GitHub branch protection, Vercel deployment protections, Supabase RLS templates, paid SaaS features behind upgrade walls, region-locked APIs, beta-only endpoints.

### Known Tensions
Adding a vendor-policy precondition assertion to every review gate is overhead that mostly produces "yes, available" on most projects most of the time; the cost-benefit only justifies itself when paid plans, regional restrictions, or feature flags are common in the project's vendor surface. Also: vendor policies change asynchronously — an assertion that passes at review time can become wrong by execution time.

### Open to Revision When
- Vendor SDKs and API responses surface plan-availability metadata structurally so the assertion can be machine-checked rather than reviewed.
- Project context evolves to a high-trust deployment posture (e.g. enterprise plan with everything pre-enabled) where the precondition is structurally guaranteed.
