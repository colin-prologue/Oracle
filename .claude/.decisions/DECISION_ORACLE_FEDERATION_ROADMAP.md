# Decision Oracle — Federation Roadmap (Corp Track)

**Status:** Pre-spec. This roadmap breaks the federation scout doc into
appropriately-scoped slices that can each become a SpecKit `/specify` pass.

**Relationship to other docs:**

- **`DECISION_ORACLE.md`** — the canonical solo-user architecture. Its
  Phase 6 ("Team Extension") roadmap entry is intentionally a stub. This
  doc is where the team/corp work actually lives.
- **`DECISION_ORACLE_FEDERATION.md`** — the architectural scout. This
  roadmap operationalizes that scout. If the scout is "what we're
  building," this is "in what order."

**Branching convention:**

- `corp` is the long-lived integration branch for all federation work.
  It branches off `main` and is intentionally not merged back until the
  trial is validated.
- Every spec below gets its own feature branch off `corp` (e.g.
  `corp/spec-1-capture-metadata`).
- Specs merge into `corp`. Only `corp` ever merges into `main`, and
  only after the trial is validated end-to-end.

This keeps experimental corp work out of `main` until it's proven.

---

## Pre-Spec Decision Blockers

These are not specs. They are decisions the user needs to make (or
investigate) before specs that depend on them can be elaborated. None
require code; all are answerable in conversation or with a short
investigation.

| # | Decision | Blocks | Notes |
|---|---|---|---|
| **D1** | **Hosted replica implementation choice** — self-hosted (your infra), Hindsight Cloud (vendor), or thin custom service wrapping the existing daemon? | S2, S3, S4 | Driver: time-to-trial. Hindsight Cloud is fastest if it natively supports the replica/federation pattern. Otherwise a thin custom service is probably right. Investigation: 1–2 hours reading Hindsight Cloud docs / asking the Hindsight team. |
| **D2** | **Asker-pays mechanics under Claude Enterprise.** Is delegated-credential synthesis feasible (hosted replica accepts asker's CE token), or does the replica need its own service account with separate cost-allocation? | S4 | Affects whether the hosted replica needs CE access at all. Investigation: read CE auth model. If delegation isn't supported, fall back to per-asker service accounts with cost-center tagging. |
| **D3** | **Sync direction (local ↔ hosted-replica).** One-way (local → replica) confirmed? Or are there bidirectional cases (e.g. replica-side capture from a phone-friendly UI later)? | S3 | One-way is much simpler and matches the trial scope. Bidirectional opens conflict resolution that isn't worth solving yet. Recommend: explicit one-way for the trial, document as a constraint. |

---

## Specs

Each spec below is intended to be small enough that `/specify` produces
a coherent plan from it. Dependencies are listed; do not start a spec
until its dependencies are merged into `corp`.

### S1 — Capture-time metadata schema extension

**Branch:** `corp/spec-1-capture-metadata`
**Depends on:** nothing
**Blocks:** S5, all "future" archetypal/hub work

**Scope.** Extend PHI capture (and OBS where reasonable) to require
new metadata fields at retain time:

- `discipline` / `role` (engineering, QA, design, production, ops, etc.)
- `org` and `team` (free-text for the trial; structured later)
- `domain` is already captured — confirm consistency

**Why first.** This is the only thing in the entire roadmap that
*can't be backfilled* without painful manual work. Every PHI captured
without these tags is a PHI that has to be re-tagged later. Shipping
this first protects the corpus.

**Deliverables.**
- Updated PHI schema in `DECISION_ORACLE.md` and the PHI markdown template.
- `/oracle-debate` and `/oracle-observe` skill prompts updated to
  collect the new fields during capture.
- Migration: a one-pass tagging exercise over existing PHIs. Can be
  manual (probably <30 PHIs at this point) — no automated migration
  needed.

**Exit criteria.** All new captures collect the fields; existing PHIs
are tagged; recall queries can filter on `discipline`.

**No federation involvement.** This spec ships value to the solo user
on day one (better recall filtering) and unblocks future federation
work without committing to it.

---

### S2 — Identity & minimal auth model

**Branch:** `corp/spec-2-identity-auth`
**Depends on:** D1 (because the auth surface lives wherever the hosted
replica lives)
**Blocks:** S3, S5

**Scope.** Define the peer identity model and ship trial-grade auth.

- Identity record shape: `{user_id, email, sso_subject?, display_name,
  discipline?}`. `sso_subject` nullable in the trial; populated when
  Microsoft SSO is wired (future).
- Trial auth mechanism: email + signed token (or equivalent
  lightweight scheme). Specifically NOT Microsoft SSO yet — that's a
  later upgrade — but the data model must accommodate it without
  schema changes.
- Auth boundary: the hosted replica is the auth-enforcing surface.
  Local daemons remain trust-the-laptop.

**Deliverables.**
- Identity schema documented.
- Trial auth flow implemented at the hosted replica layer.
- Migration plan for trial → SSO (future) sketched, not implemented.

**Exit criteria.** A peer can authenticate to the hosted layer, be
identified, and have their requests rate-limited / logged.

---

### S3 — Hosted replica MVP

**Branch:** `corp/spec-3-hosted-replica`
**Depends on:** D1, D3, S2
**Blocks:** S4

**Scope.** Stand up the hosted replica surface, with one-way sync
from local daemon to replica.

- Replica instance per user (or per-user namespace within a shared
  deployment, depending on D1).
- Sync: local daemon → replica. Mechanism depends on D1 (push from
  local, pull from replica, or shared bank backend).
- Replica exposes a recall endpoint identical to the local daemon's.
- Solo functionality unaffected: local daemon remains canonical.

**Deliverables.**
- Replica deployment runbook.
- Sync mechanism implemented.
- Replica recall endpoint matching local daemon's contract.
- Health/observability: a peer can confirm their replica is in sync.

**Exit criteria.** A peer's replica returns the same recall results
as their local daemon (subject to sync lag), and remains reachable
when the laptop is offline.

**Out of scope for this spec.** Federation queries, asker-pays,
synthesis at the replica. Replica is recall-only here. Synthesis
joins in S4.

---

### S4 — Federation protocol & synthesis path

**Branch:** `corp/spec-4-federation-protocol`
**Depends on:** D2, S3
**Blocks:** S5

**Scope.** Define and implement the cross-oracle query protocol.

- Endpoint: `POST /v1/federation/oracles/{peer_id}/query`
- Request: `{question, asker_id, auth_token}`
- Response: `{answer, oracle_id, ts}` (citations are a future
  extension — see F1).
- Synthesis runs against the asker's CE credentials (per D2). If
  delegation is infeasible, fall back is documented but not
  implemented in this spec.
- Authoring side (this spec): the protocol on the replica. Calling
  side ships in S5.

**Deliverables.**
- Federation endpoint on the hosted replica.
- Asker-pays synthesis flow.
- Audit log of every cross-oracle query.

**Exit criteria.** A peer's replica accepts authenticated queries
from another peer and returns synthesized answers. Asker's CE quota
is what's consumed.

---

### S5 — `/oracle --from <peer>` & directory

**Branch:** `corp/spec-5-targeted-query-skill`
**Depends on:** S1, S2, S4

**Scope.** The user-facing surface for cross-oracle queries.

- Extend `/oracle` skill to accept `--from <peer>` (one or more peers).
- Directory endpoint: list of available oracles with discipline tags.
  Backs name resolution; suggests-but-does-not-route.
- `/oracle "..." --from alice,bob` returns per-peer answers (no
  aggregation in the trial; aggregation is a separate, deferred spec).
- Same skill in MCP form for non-CC clients (mirroring the existing
  `oracle_query` MCP server pattern).

**Deliverables.**
- Updated `/oracle` skill with `--from` support.
- Directory endpoint.
- MCP federation tool (optional — confirm during scoping).

**Exit criteria.** From a session, a user can target a specific peer
by name and get a synthesized answer. Default `/oracle` (no `--from`)
behavior is unchanged.

---

### S6 — Onboarding & migration tooling

**Branch:** `corp/spec-6-onboarding`
**Depends on:** S5

**Scope.** A new peer can join the trial in <30 minutes without
hand-holding.

- Onboarding script: provisions hosted replica, configures local
  daemon to sync, registers identity, seeds directory entry.
- Migration for existing solo users: bring their corpus into the
  trial without re-capturing.
- Documentation: peer-facing setup guide.

**Deliverables.**
- Onboarding CLI / runbook.
- Solo → trial migration verified end-to-end.

**Exit criteria.** A new peer joins, captures their first PHI, has
it visible to others via `/oracle --from`, and can query a peer's
oracle — all from scratch, in one sitting.

---

## Future / Deferred

These are tracked here so they don't get lost, but they are not next.
Most belong post-trial; a few are independent enhancements.

| ID | Name | Notes |
|---|---|---|
| **F1** | Citations in federation response | Extend S4's response with cited PHI/OBS IDs and short snippets. Audit + cross-learning. Additive to the protocol; no breaking change. |
| **F2** | Microsoft SSO upgrade | Replace trial auth with Entra/Azure AD. Identity schema already accommodates it (S2). Pure-ops upgrade. |
| **F3** | `/challenge` command | Adversarial probe against your own (or a peer's) PHIs/OBSs. Surfaces blandness, contradictions, edge cases. Independent of federation but benefits from richer metadata. |
| **F4** | Hub / consensus synthesis | Periodic synthesis across replicas → an org-level "house consensus" bank. Per-user banks preserved for dissent. Needs real corpus first. |
| **F5** | Discipline archetypes | Three flavors (curated / synthetic / persona). Decide which after F4 reveals what convergence actually looks like. |
| **F6** | Broadcast & aggregation queries | `/oracle "..." --org` fans out to all reachable peers. Aggregation strategy is its own design problem. |
| **F7** | Smart routing | System suggests who likely has signal on a topic based on discipline + recent capture activity. Below F6 in priority. |
| **F8** | Content-class detection at capture | Automated check that captures don't drift outside the engineering scope. Trial relies on social/process control; revisit if scope drifts. |

---

## Sequencing Notes

**Critical path:** S1 → S2 → S3 → S4 → S5 → S6.

S1 is the only spec that can ship before any decisions land — start
there regardless of what else is in motion.

D1 (hosted replica choice) is the highest-leverage blocker. Resolving
it unlocks S2, S3, and S4.

**Parallelizable:** Once D1 is resolved, S2 and S3 can run in parallel
(different surfaces). S4 needs S3.

**Validation gate before merging `corp` to `main`:** S6 exit criteria
must hold for at least two real peers (not just the author) for at
least two weeks of normal use. If that bar isn't met, `corp` stays
unmerged and the work continues.
