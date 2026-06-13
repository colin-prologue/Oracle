<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

OBS-007: Vector recall earns its marginal value at session cold starts, not mid-session warm context.

When a project's entire decision corpus fits comfortably in a few direct file reads, semantic search over that corpus duplicates what the reads already provide — the model already has the content. The unique contribution of vector recall is cross-session: surfacing content from a prior session that the current session would otherwise miss entirely.

This asymmetry has two practical implications:
1. Recall-before conventions in workflow skills (e.g., speckit.plan calling memory_recall before generating a plan) add real value only if the session starts cold without the relevant files pre-loaded. In warm sessions where ADRs and specs are already in context, the recall step is redundant.
2. The case for maintaining a local vector index weakens as the corpus shrinks and the session workflow pre-loads files anyway. The index earns its keep proportionally to (corpus size) × (session cold-start frequency).

Observed in Claude-Root: the memory server's recall-before convention provided near-zero marginal value because sessions routinely read the spec/ADR files directly, and the corpus (63 records) was small enough to fit in context. The oracle bank avoids this trap because it captures conversational reasoning that never lands in committed files — content the next session genuinely cannot access any other way.
