<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-018 — Format-as-UX Needs Real-Surface Review

**Date:** 2026-04-30
**Domain:** process
**Source Project:** TravelPlanner
**Source:** Feature 015-coverage-ci-gate's `comment-markdown.md` contract pinned cell formatting (`26.42`, `±0.00`, `26`) and was locked in by 5 byte-exact fixtures plus four review gates. The first time it rendered against a real PR comment, the project owner immediately spotted that bare numbers are not self-documenting and asked for `%` suffixes. Captured as LOG-047 (coverage_comment_percent_suffix); the fix shipped in 24 hours via a one-commit PR.

### Philosophy
Frozen contracts and byte-exact fixtures protect against drift but do not protect against the contract itself being subtly wrong. Format-as-UX needs human eyes on the rendered surface in production at least once before the feature is declared done — the first real render is the first time a non-author sees the output in context, and review gates cannot replicate that.

### Why I Hold This
Review gates evaluate the contract; they cannot evaluate the contract's legibility to a non-author reading the rendered output later. Fixtures lock in *what* the format is, not *whether it is right*. The cost of a deliberate "look at it once" step is one PR-comment-load or one log-tail; the cost of catching a format flaw post-launch can be much higher when it has to ship as an amendment with cascading documentation updates.

### Where It Applies
Any feature whose output is read by humans: PR comments, error messages, terminal banners, email templates, generated reports, dashboard chrome, log lines, push notifications, IDE squiggles, AI-generated UI strings. Strongest fit when the audience is non-technical, when the output is read at a glance rather than parsed, or when the rendering happens in a context different from the testing surface.

### Known Tensions
For features with high frequency and well-trodden output formats (standard syslog lines, conventional API error responses), the marginal value of a real-surface review is low because the format is constrained by external convention. Also: the "look once" step adds a checkpoint to the close-out checklist that can be skipped under deadline pressure unless the workflow makes it explicit.

### Open to Revision When
- Snapshot-based UX testing tools become precise enough to capture rendering-context legibility (typography, color, spacing, surrounding chrome) such that a contract test can stand in for a human read.
- Output formats are produced by AI assistants that critique their own legibility against an explicit rubric before shipping, internalizing the human-eyes step into the generation pipeline.
