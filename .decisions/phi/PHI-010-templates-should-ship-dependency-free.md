<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-010 — Templates ship free of author residue: no dependencies, no dogfood

**Date:** 2026-04-24
**Revision:** 2026-07-06 — consolidation pass 1: absorbed PHI-022 (separate dogfood by filesystem) as a named corollary; scope tightened to reusable scaffolds
**Domain:** architecture, tooling
**Source Project:** Claude-Root (corollary from mini-fax)
**Source:** Removing the vector memory server from the Claude-Root speckit template reduced its dependency footprint from Python/uv/Ollama/LanceDB/FastMCP to zero, making it immediately usable on any project.

### Philosophy
A reusable template's value degrades with every piece of author-serving content it carries. That content takes two forms: runtime dependencies — infrastructure choices that served the template author become adoption friction for every downstream user; optional capabilities belong in separate, opt-in layers — and dogfood artifacts — the template's own roadmaps, real specs, working decision records, and internal docs, which accumulate whenever a scaffold is used to develop itself. Scope: this governs reusable scaffolds, starter kits, and templates — things other projects copy — not ordinary in-project dependency or tooling choices.

### Corollary
- **Separate dogfood from scaffold by filesystem, not convention (ex-PHI-022, merged 2026-07-06):** adoption friction is a function of the worst plausible path users take, not the supported one. Install scripts with allowlists and README disclaimers protect only supported-path users; `git clone` is the natural-but-unsupported path and inherits every artifact in the template's working tree. Encode the dogfood/template boundary in the filesystem — a `_template-author/` directory or two separate repos — so both paths produce clean adoption. Boundaries: single-repo dogfooding is ergonomically real and its friction is invisible to the author until adoption scale; adopters may legitimately want real example specs as reference material, which complete separation removes.

### Why I Hold This
The Claude-Root template required Ollama, LanceDB, FastMCP, Python 3.10+, and uv just to use the speckit workflow — none of which had anything to do with the workflow itself; extracting the memory server to an archive branch eliminated the barrier entirely. The same template, cloned rather than installed, handed mini-fax the template's own 199-line internal roadmap, two real feature spec directories, and an internal optimization doc that all looked like part of the template until carefully audited. Dependencies and dogfood are one failure — author-serving content shipped to adopters — at two grains.

### Evidence
- Claude-Root memory-server extraction, 2026-04-24 (founding incident)
- Claude-Root → mini-fax bootstrap inheritance via `git clone`, 2026-05-19 (supports, ex-PHI-022 grounding)
- OBS-017 — canonical-vs-operative artifact split (supports, ex-PHI-022 grounding)

### Where It Applies
Starter kits, scaffolding tools, project templates, boilerplate: speckit-style workflow templates, framework generators, cookiecutter/copier templates, GitHub template repos, IaC modules shipping example deployments, plugin/extension scaffolds, design-system repos doubling as documentation sites. Most load-bearing when the template's purpose is process or convention, not a tech demo of a specific dependency.

### Known Tensions
Some templates are explicitly demos of a specific technology (a React starter should have React) — the principle is least applicable when the dependency IS the point. Complete dogfood separation removes demonstration value. Splitting repos imposes cross-tree coordination costs the author pays daily for friction adopters pay rarely.

### Open to Revision When
A dependency becomes universally available with zero setup. The install-script path becomes so dominant the clone path is genuinely never used. The template surface is too tiny to accumulate residue. An install-time scanner can reliably detect author residue, making convention-based separation enforceable rather than aspirational.
