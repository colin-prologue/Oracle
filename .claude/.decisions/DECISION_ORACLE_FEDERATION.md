# Decision Oracle — Multi-Tenant Federation Scout

**Status:** Scout (pre-spec). This doc captures the architectural shape of moving the
Oracle from a single-user tool into a peer-shared system with a path to enterprise.
It exists to scope the problem before any `/specify` pass — not to commit to an
implementation. A SpecKit spec should follow only after the open questions at the
bottom are resolved.

**Relationship to `DECISION_ORACLE.md`:** This is the deeper dive into Phase 6
("Team Extension") of that doc's roadmap. The single-user architecture described
there is unchanged for solo use; this doc only covers what's added when peers
enter the picture.

---

## Goals

In priority order:

1. **Self-acceleration first.** Personal oracles speed up individual work queues
   and let the user delegate repeated decision-making. Federation is downstream
   of this working well solo.
2. **Peer extension.** Other engineers can run their own oracle and accumulate
   their own PHIs/OBSs without coordinating with anyone else.
3. **Cross-oracle querying on the fly.** From a session, target a specific peer's
   oracle to get a different perspective on a decision.

Federation is a **read-side** capability. Capture (debate/observe/synthesize)
remains personal and explicit, consistent with PHI-003.

---

## Non-Goals (for the trial)

- A shared/team oracle bank.
- Auto-aggregation across peers (broadcast queries, "ask everyone").
- Synthesizing a hub/consensus oracle from the corpus.
- Discipline-archetype oracles (QA / production / design / engineering personas).
- Storing personnel, HR, or otherwise sensitive content. Oracle scope is
  engineering, architecture, projects, and engineering-discipline meta-patterns
  only. This is policy, not just convention — see "Content Scope Policy" below.

These are deferred deliberately. See "Deferred — revisit after personal oracles
work well at team scale" at the bottom.

---

## Phasing

| Phase | Scope | Audience | Status |
|---|---|---|---|
| **0 — Solo (today)** | Local daemon, single user, local PHI files | Colin only | Shipped |
| **1 — Peer trial** | Per-user oracles + hosted replicas + targeted cross-oracle query | Small peer group (5–20) | This scout |
| **2 — Team rollout** | Same shape, hardened auth, observability, onboarding flow | Department (10–50) | Same arch as Phase 1 |
| **3 — Enterprise** | SSO-integrated, security review, formal data classification | Org-wide | Same arch, ops-hardened |

Phases 1 → 3 share the **same architecture**. The progression is operational
maturity (auth, isolation, observability, support), not a re-architecture.
That's the central design constraint of this scout: pick a shape now that
survives the climb to enterprise without rework.

---

## Architectural Shape

### Per-user oracles, federated

Each peer has their own oracle. Banks are not shared. Cross-oracle visibility
is achieved by querying another peer's oracle through a stable protocol, not
by reading their data.

**Why this shape (resolved during scout):**

- Convergence is real and probably a feature — peers in the same org will
  overlap on the "obvious" answers. The signal in cross-querying lives in
  the *disagreements* and personal heuristics. Per-user banks preserve that
  dissent surface.
- Shared corpora pollute easily and create governance problems early.
  Per-user banks defer that question until there's data to argue over.

### Two deployment surfaces per user

| Surface | Owns | Always-on? | Purpose |
|---|---|---|---|
| **Local daemon** (existing) | Authoring, capture, solo queries | No (laptop sleeps) | Unchanged from Phase 0 |
| **Hosted replica** (new) | Federation read-path | Yes | Answers cross-oracle queries when laptop is offline |

Solo use stays entirely on the local daemon — no hosted dependency for
single-user value. The hosted replica only matters when peers are involved.
This boundary is intentional: it lets the trial begin without forcing solo
users to onboard infrastructure.

The local daemon is the source of truth for capture. The hosted replica is
a synced read-side mirror.

### Federation protocol

Cross-oracle queries are **synthesized question-in / answer-out**. A query
produces a natural-language answer from the target oracle's synthesizer, not
raw PHIs/OBSs.

```
POST /v1/federation/oracles/{peer_id}/query
{ "question": "...", "asker": "...", "auth": "<sso-token>" }
→ { "answer": "...", "oracle_id": "alice", "ts": "..." }
```

**Why answer-not-raw:** decouples the protocol from each oracle's schema and
local quirks. Peers can evolve their bank internals (tags, metadata, custom
skills) without breaking the wire format. The answer is what's portable.

**Future extension:** include cited PHI/OBS identifiers and short snippets
in the response for auditing and cross-learning. Defer until the basic
protocol is in use; the citation layer is additive.

### Targeted, not broadcast

Cross-oracle queries are explicit and targeted: `/oracle "..." --from alice`.
The default `/oracle` path always asks your own oracle first.

**Why not broadcast:** broadcast forces governance, attribution, and
reconciliation problems on day one — exactly when there's no data to inform
those choices. Targeted querying is also how the user actually thinks about
it: "I want Alice's view on this," not "I want the org's view on this."

### Identity & auth

**Microsoft SSO** (Entra/Azure AD) is the assumed identity layer — it's the
universal SSO in the target org. Claude Enterprise is the assumed LLM access
layer for synthesis. The two are independent: SSO authenticates the asker;
Claude Enterprise provides the model.

For the early trial, a thinner mechanism (email + token) is acceptable as
long as it doesn't shape the data model in a way that blocks the SSO upgrade.
Recommended: model peers as `{user_id, email, sso_subject}` from day one,
even if `sso_subject` is null in the trial.

### Cost attribution

**Asker pays.** When Bob queries Alice's oracle, Bob's Claude Enterprise
quota covers the synthesis. The hosted replica should be designed so that
synthesis runs under the asker's credentials, not the answerer's. This
prevents one popular oracle from burning the owner's quota and aligns
incentives — querying isn't free, so peers ask deliberately.

Implementation note: this likely means the hosted replica accepts a
synthesis token / delegated credential from the asker rather than running
synthesis under a service account billed to the answerer. Worth confirming
this is feasible under Claude Enterprise's auth model before locking it in.

### Schema & protocol stability

The federation protocol must stay stable across all oracles. Local bank
schema can evolve per user. **Mandatory metadata at PHI capture time:**

- `discipline` / `role` (engineering, QA, design, production, etc.)
- `domain` (architecture, tooling, process, infrastructure — already exists)
- `org` / `team` (for future scoping)

Capturing these from day one keeps three downstream possibilities open
without committing to any of them: discipline archetypes, team-scoped
hubs, and synthesis filters. Without these tags, all three require
backfill or rebuild.

---

## Content Scope Policy

The Oracle is for engineering content: projects, architecture, engineering
disciplines, tooling, process, infrastructure. **It is not for:**

- Personnel matters, performance, hiring, comp.
- Customer-identifiable or otherwise sensitive business data.
- Any content that would be inappropriate to surface to a peer who happens
  to query your oracle.

Because the trial uses an open-within-org permission model (anyone in the
org can query any peer's oracle), this policy is the privacy guarantee.
PHI capture flows should reinforce it; oracle-debate and oracle-observe
prompts should remind authors of the scope before retain.

A future hardening pass might add automated content-class detection at
capture, but for the trial, the social/process control is sufficient.

---

## Permission Model

**Open within the org.** Any authenticated peer in the same org can query
any other peer's oracle. No allowlists, no team-scoping at the trial.

This works *because* of the content scope policy above. If the oracle held
sensitive content, open-within-org would be wrong. Because it doesn't, the
overhead of allowlist management buys nothing and slows adoption.

Revisit if: (a) content scope is broadened, (b) a peer wants to opt out
of being queried, or (c) external (cross-org) federation comes into scope.

---

## Discovery UX

`/oracle "..."` — your own oracle, unchanged.
`/oracle "..." --from alice` — Alice's oracle.
`/oracle "..." --from alice,bob` — multiple peers, results returned per-peer
(no aggregation in the trial; aggregation is a Phase 2+ question).

A directory of available oracles (probably a simple list endpoint on the
hosted service) backs name resolution. Directory entries carry the
discipline/role tag so a future routing UI can suggest who to ask, but the
trial does not include smart routing — picking a peer is a deliberate act.

---

## Future Capability — `/challenge`

Adversarial probe against your own (or a peer's) PHIs and OBSs. Goal:
surface where a held opinion gets bland, contradicts itself, or breaks
under edge cases. Prevents the corpus from drifting into generic
platitudes as it grows.

Out of scope for the trial. Listed here so the data model — especially
the role/domain tagging above — is friendly to it later.

---

## Open Questions (resolve before `/specify`)

| # | Question | Notes |
|---|---|---|
| 1 | **Local ↔ hosted-replica sync semantics.** One-way (local → replica) or bidirectional? What happens if a peer captures a PHI while their laptop is offline and the replica answered an inconsistent query in the meantime? | Likely one-way (local is source of truth, replica is read-only mirror) but worth explicit confirmation. Eventual consistency is probably fine given asker-pays and the absence of writes through the replica. |
| 2 | **Migration path for current solo users.** Today the canonical PHI directory is `${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}/.decisions/phi/`. When a solo user joins the trial, what migrates: just bank contents, or PHI files too? Where do PHI files live in the hosted world? | Probably: solo PHI files stay in the user's Hindsight repo as today; the hosted replica syncs from the bank only. Files remain canonical-on-disk for the owner; they are not replicated. |
| 3 | **Asker-pays mechanics under Claude Enterprise.** Is delegated-credential synthesis actually feasible under CE's auth model, or does the hosted replica need a service account that gets billed back via separate cost-allocation? | Resolve before architecting the synthesis path. Affects whether the hosted replica needs Claude API access at all or just orchestrates against the asker's session. |
| 4 | **Identity resolution.** Microsoft SSO for the enterprise path; what for the trial? Email + token is probably enough, but the data model should anticipate `sso_subject`. | Trial-pragmatic answer: ship with email-based identity, store an optional `sso_subject` field, populate when SSO is wired. |
| 5 | **Hosted replica implementation.** Self-hosted (your infra), Hindsight Cloud (vendor), or a thin custom service that wraps the existing daemon? | Affects time-to-trial. Hindsight Cloud is fastest if it supports the replica/federation pattern; otherwise a thin custom service is probably the right answer. |

---

## Deferred — revisit after personal oracles work well at team scale

These are explicitly out of scope for Phases 1–2 and listed so they're not
forgotten:

- **Convergence handling & dissent preservation.** As oracles align on
  org-style "obvious" answers, the value migrates to the disagreements.
  Need a UX or synthesis pattern that surfaces dissent rather than
  averaging it away.
- **Hub oracle / consensus synthesis.** Periodic synthesis across the
  hosted replicas to produce an org-level "house consensus" bank,
  separate from per-user banks. Feasible because replicas already hold
  the data.
- **Discipline archetypes.** Three flavors, each with different
  tradeoffs:
  - *Curated* — a senior practitioner maintains an authoritative oracle
    for their discipline. Authoritative but bottlenecked.
  - *Synthetic* — derived from role-tagged PHIs of practitioners in
    that discipline. Scales but risks caricature.
  - *Persona* — a system prompt with no bank backing. Cheap, but
    generic.
  The role/discipline metadata captured in Phase 1 is what keeps these
  options open.
- **`/challenge` command.** Adversarial probe to stress-test held PHIs.
- **Broadcast / aggregation queries.** Ask the org, not a single peer.
- **Smart routing.** System suggests who likely has signal on a topic.

---

## Recommended Next Step

Resolve the five open questions above (mostly via conversation, not
investigation), then run `/specify` against the resulting shape. The
spec should target Phase 1 (peer trial) only — Phases 2 and 3 share
the architecture and reuse the same spec under different operational
constraints.

The scout doc itself should not be the spec. Its job is to make the
spec faster and narrower by retiring forks before they show up as
ambiguity in the elaboration loop.
