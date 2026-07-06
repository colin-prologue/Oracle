<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

## OBS-027 — Balance harness variance in sampling layer, sim untouched
**Relationship:** supports PHI-045

On 2026-07-04/05, rts-proto's Gate 7 balance harness needed outcome variance from a deterministic sim whose seed was inert (nothing drew from state.rng). The decision record (docs/decisions/balance-sampling.md) put variance in the sampling layer — seeded ±2 spawn jitter at scenario construction, both orientations per seed — leaving step() untouched and all committed goldens standing, verified in-gate. Prior-art research reinforced the line: StarCraft: Brood War (1/256 base miss + 136/256 uphill), C&C Tiberian Dawn (Random_Pick projectile scatter, per the GPL source), Warcraft 3 (damage dice), and AoE2 (accuracy rolls) all placed randomness in-sim only as a game-design feature, never for measurement; balance itself was mass playtesting. The harness's first 1000-run report then surfaced a real sim defect — grunts win 57% as player 0 vs 84% as player 1 (within-tick movement-order aim advantage) — which was filed as design-debt issue #4 requiring its own decision record and deliberate golden re-record, not patched in the harness or the sim.
