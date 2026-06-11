<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-022 — Templates accumulate author-only residue; separate dogfood from scaffold by filesystem, not convention

**Date:** 2026-05-19
**Domain:** tooling
**Source Project:** mini-fax (surfaced via Claude-Root template adoption)
**Source:** mini-fax bootstrap inherited Claude-Root's own roadmap.md (199 lines about the template's internal feature backlog), `specs/000-review-benchmark/`, `specs/001-review-efficiency-profiler/`, and `docs/speckit-optimization-recommendations.md` because `git clone` was used instead of `setup.sh`. The supported install path filters correctly; the natural unsupported path doesn't.

### Philosophy
When a scaffold or template is used to develop itself, dogfood artifacts (real roadmaps, real specs, working decision records, internal optimization docs) accumulate alongside the reusable machinery. Encode the dogfood/template boundary in the filesystem (a `_template-author/` directory, or two separate repos) so the supported install path AND the unsupported clone path both produce clean adoption.

### Why I Hold This
Adoption friction is a function of the worst plausible path users take, not the supported one. Conventions (install scripts with allowlists, README disclaimers) only protect users of the supported path. The Claude-Root → mini-fax bootstrap demonstrated that `git clone` is the natural-but-unsupported path, and it inherited every artifact in the template's own working tree — including a roadmap, two real feature directories, and an internal optimization doc that all looked like part of the template until they were carefully audited. The filesystem boundary is the only one that survives a user choosing the wrong adoption path.

### Where It Applies
- Project templates / starter kits (Yeoman, create-react-app, Vite templates, copier templates, Spec-Kit, Cookiecutter)
- IaC modules with their own example deployments (Terraform modules, Pulumi components, Helm charts shipped with values examples)
- Plugin/extension scaffolds (VS Code plugin templates, browser-extension boilerplates)
- Design system repos that double as documentation sites
- ESLint/Prettier configs that ship with their own internal config
- Any repo where the same codebase is BOTH "the thing to copy" AND "the thing where its authors do their development"

### Known Tensions
- Single-repo dogfood loops are immediate and ergonomic: edit template + use template + commit all in one place. Splitting into two repos (or even one repo with a `_template-author/` subtree) imposes cross-tree coordination.
- Adopters may legitimately want to see real example specs / decision records as reference material; complete separation removes the demonstration value.
- Until adoption scale justifies the split, the dogfood-in-the-template friction is mostly invisible to the original author.

### Open to Revision When
- The install-script path becomes so dominant that the clone path is genuinely never used (unlikely; "just clone the repo" is a default human reflex).
- The template surface is so tiny that no author-only artifacts can accumulate (e.g., a single config file with no roadmap).
- A scanner or hook can reliably detect "this file looks like author residue" at install time — making convention-based separation enforceable rather than aspirational.
