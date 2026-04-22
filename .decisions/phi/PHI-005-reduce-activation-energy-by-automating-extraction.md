<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-005 — Reduce Activation Energy for Sustained Habits by Automating Extraction, Not Execution

**Date:** 2026-04-18
**Domain:** tooling / process
**Source Project:** hindsight
**Source:** oracle-observe required articulating the insight before capturing it. Sessions ended with `/clear` and nothing was retained because the habit required a non-trivial step (naming the pattern) that was easy to skip. oracle-preclear inverts this: Claude extracts candidates automatically, user approves or skips.

### Philosophy
When a habit requires the user to articulate something before acting, make the extraction automatic and reduce the job to approval. Activation energy is the enemy of consistent capture — extract first, judge second.

### Why I Hold This
Knowledge capture workflows that require insight articulation before capture have a structural weakness: the hardest moment (recognizing and naming a pattern) is also the trigger. When that moment is skipped — due to fatigue, context switch, or urgency — nothing is captured. Moving extraction before judgment eliminates the hardest step from the critical path.

### Where It Applies
Any capture, logging, or retention system where the user must recognize and articulate a pattern as a prerequisite: decision logs, retrospectives, code review notes, session summaries, incident postmortems. The pattern is: replace "notice → articulate → capture" with "auto-extract → review → approve/skip."

### Known Tensions
Automated extraction produces noise alongside signal. The approval step is only low-friction if the proposals are high-quality — bad proposals create review fatigue that's worse than the original manual habit. The investment in making the extractor good is the real cost.

### Open to Revision When
If proposal quality degrades (too many irrelevant candidates per session), reconsider whether the extractor has enough context to do useful work, or whether manual articulation with better tooling (templates, prompts) is lower total friction than reviewing poor proposals.
