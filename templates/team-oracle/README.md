<!-- TEMPLATE — this directory is a skeleton for a standalone repo. Copy it out
     and `git init` it in your target environment; do not use it in place.

     Two paths are intentionally de-fanged so this template can live nested
     inside another repo without Claude Code discovering them (skill-name
     shadowing, nested-CLAUDE.md injection). After copying out, activate them:

       mv dot-claude .claude
       mv CLAUDE.template.md CLAUDE.md
-->

# Team Decision Oracle

A file-based team memory for engineering decisions. It captures **philosophies**
(PHI — held opinions that would change your default on a new project) and
**observations** (OBS — patterns noticed across work, with cited evidence), and
surfaces them inside Claude Code sessions at the moment decisions get made.

No servers, no API keys, no database. The repo is the system:

- **Records** are immutable markdown files, one per record (`records/phi/`, `records/obs/`).
- **Retrieval** is an index-scan skill (`/oracle`) — Claude reads `INDEX.md`, picks
  candidates, reads only those files, and synthesizes an answer with citations.
- **Governance** is pull requests — a PHI is *proposed* on a branch and becomes
  *adopted* when a reviewer approves the merge.
- **Habit** is a SessionStart hook that syncs the clone and injects the index
  into every session's context.
- **Capture** is human-gated: a weekly miner drafts candidates from your local
  Claude transcripts into `inbox/` (gitignored, private), and `/oracle-triage`
  promotes only what you approve.

## Quickstart

```bash
git clone <your-remote> ~/team-oracle
cd ~/team-oracle && ./scripts/install.sh    # symlinks skills, prints hook snippet
export ORACLE_ROOT="$HOME/team-oracle"       # add to your shell profile
```

Then, in any Claude Code session:

```
/oracle "Should this service own its schema or share the platform DB?"
```

## Record lifecycle

| Stage | Mechanism |
|---|---|
| Draft | `/oracle-debate` (PHI) or `/oracle-observe` (OBS) writes the file on a branch |
| Propose | Open a PR; the record ships with `Status: proposed` (PHI) or `active` (OBS) |
| Adopt | PR approval + merge flips a PHI to `adopted`; disagreement worth keeping merges as `contested` |
| Graduate | An OBS cited repeatedly in query logs is a PHI candidate — run `/oracle-debate` on it |
| Retire | Status flips to `superseded → PHI-NNN` or `declined`; the file never gets deleted |

## Conventions

- **IDs** are sequential (`PHI-001`, `OBS-001`). Two branches claiming the same
  number conflict in `INDEX.md` at merge time — the later PR renumbers. That
  merge conflict *is* the collision guard; don't build anything fancier.
- **Every record PR also updates its one line in `INDEX.md`.** The index is the
  retrieval surface; a record missing from it is invisible.
- **`inbox/` never leaves your machine.** It is gitignored because miner drafts
  come from raw session transcripts and may contain confidential context. Only
  triaged, human-approved text reaches a branch.
- **Query logs** (`queries/YYYY-MM.<user>.jsonl`) are per-user append-only files
  — per-user so they never merge-conflict. They exist to answer "which records
  actually get used?", which drives OBS→PHI graduation.
- **PHIs are owned opinions, not laws.** Each names a sponsor. Two contested
  PHIs pointing opposite directions, each with evidence, is a healthy state.

## Seeding

Do not invite the team until ~10 genuinely useful records exist. The first
query a teammate runs decides whether they ever run a second one.

`SEED.md` is an optional starter corpus of portable principles distilled from
prior projects — a shortcut to those first ~10 records. Don't bulk-copy it into
`records/`; adopt entries one at a time through `/oracle-debate` or
`/oracle-observe` so each enters via the normal propose→adopt lifecycle with
your team as sponsor (its header explains the drill). Delete or keep the file
afterward — `/oracle` never reads it.

## Known open items

- Hook scripts are bash; on Windows they need Git Bash or WSL, or a PowerShell port.
- The index-scan retrieval reads every index line into context. Fine to a few
  hundred records; revisit (e.g., domain-sharded indexes) only when that breaks.
