# SpecKit Step-Level Hooks: Oracle Integration Design

## What this is

A design for adding step-level hooks to SpecKit commands — hooks that fire at specific
decision points *within* a command, not just before/after the whole command runs.

The immediate use case is oracle integration: automatically querying the Decision Oracle
before SpecKit asks a clarifying question, so relevant prior patterns surface without
any manual prompting.

The mechanism is general-purpose. Oracle is the first consumer, but any extension can
register for these hooks.

---

## Why command-level hooks aren't enough

SpecKit already has `before_clarify` / `after_clarify` hooks via `extensions.yml`. These
fire before and after the whole `clarify` command. That's too coarse for oracle:

- `before_clarify`: fires before the spec has been analyzed, before any question has been
  identified. Oracle can't provide relevant context — it doesn't know what ambiguity is
  about to be surfaced.
- `after_clarify`: too late — questions have already been asked and answered.

The oracle query needs to fire immediately before each individual clarifying question is
presented to the user, when the specific ambiguity is known but the user hasn't answered yet.

---

## Design: the `before_question` hook type

Add a new hook point to `speckit-clarify`'s sequential questioning loop (step 4). Before
presenting each question to the user, the skill checks `extensions.yml` for
`hooks.before_question` entries and executes them.

This is identical to how `before_clarify` hooks work today — the same check, the same
execution model — just at question granularity instead of command granularity.

### How argument injection works (no schema change needed)

The hook YAML has a `command` field but no argument template. When SpecKit outputs
`EXECUTE_COMMAND: oracle`, Claude executes the oracle skill and — because it already knows
what question it's about to ask — synthesizes a relevant oracle query from that context.
Claude is the executor of both SpecKit and oracle; the context transfer happens implicitly.

The hook's `description` field guides what context Claude uses:

```yaml
description: Query oracle for relevant PHIs before presenting this clarifying question.
             Use the current question as the oracle query context.
```

This is sufficient. Claude reads the description and formulates the oracle query from the
question it was about to present.

---

## Implementation

### Part 1: speckit-clarify/SKILL.md change

In the **Sequential questioning loop** (step 4), add a hook-check block immediately before
the "Present EXACTLY ONE question at a time" instruction:

```markdown
4. Sequential questioning loop (interactive):
    - **Before presenting each question, check for step-level hooks:**
      - Check if `.specify/extensions.yml` exists in the project root.
      - If it exists, read it and look for entries under the `hooks.before_question` key.
      - If the YAML cannot be parsed or is invalid, skip silently and continue.
      - Filter out hooks where `enabled` is explicitly `false`.
      - For each remaining hook, output the following based on its `optional` flag:
        - **Optional hook** (`optional: true`):
          ```
          **Optional Pre-Question Hook**: {extension}
          Command: `/{command}`
          Description: {description}
          To execute: `/{command}`
          ```
        - **Mandatory hook** (`optional: false`):
          ```
          **Automatic Pre-Question Hook**: {extension}
          Executing: `/{command}`
          EXECUTE_COMMAND: {command}
          Wait for the result before presenting the question.
          ```
    - Present EXACTLY ONE question at a time.
    ... (rest of existing step 4 unchanged)
```

That's the only change to the SpecKit skill. No other files need to change.

### Part 2: oracle's extensions.yml entries

Add to `.specify/extensions.yml` in any project where oracle is active:

```yaml
hooks:
  # ... existing hooks ...

  before_question:
  - extension: oracle
    command: oracle
    enabled: true      # set false to return to manual-only oracle mode
    optional: true
    description: >
      Query oracle for relevant PHIs before presenting this clarifying question.
      Use the current question as the oracle query context.
    condition: null
```

`optional: true` means the hook is surfaced but not automatically executed — the user
sees the prompt and can choose to run it. Set `optional: false` if you want fully automatic
(no prompt, oracle fires every time before each question).

**Mode toggle:**
- Auto-oracle on: `enabled: true`
- Auto-oracle off: `enabled: false`
- Prompted (not auto): `optional: true`
- Fully automatic: `optional: false`

---

## What it looks like in practice

User runs `/speckit.clarify`. SpecKit:

1. Loads spec, runs coverage scan, generates question queue internally.
2. Before presenting Q1:
   - Checks extensions.yml, finds `before_question` oracle hook (optional).
   - Outputs:
     ```
     **Optional Pre-Question Hook**: oracle
     Command: `/oracle`
     Description: Query oracle for relevant PHIs before presenting this clarifying question.
     To execute: `/oracle`
     ```
   - User can run `/oracle "what patterns apply to [the ambiguity]"` or skip.
3. Presents Q1 (with recommendation as normal).
4. User answers. SpecKit integrates answer into spec.
5. Repeat from step 2 for Q2–Q5.

With `optional: false`, step 2 becomes:
- Oracle query fires automatically, result shown.
- SpecKit incorporates any relevant PHIs into its recommendation before presenting the question.
- No user action required.

---

## Future extension points

The same pattern applies to other SpecKit commands at their own decision points.
Add only when there's a concrete use case, not speculatively:

| Command | Hook name | When it fires | Oracle value |
|---|---|---|---|
| `clarify` | `before_question` | Before each clarifying question | Surface PHIs relevant to the ambiguity being resolved |
| `analyze` | `before_tradeoff` | Before surfacing architectural tradeoffs | Surface PHIs relevant to the tradeoff domain |
| `plan` | `before_architectural_choice` | Before committing to an architecture pattern | Surface PHIs that constrain or inform the choice |
| `specify` | `before_requirement` | Before finalizing a functional requirement | Replaces the current inline step 5a |

**Start with `clarify` only.** The pattern will prove itself (or not) before expanding.

---

## Relationship to command-level hooks

Step-level hooks complement, not replace, command-level hooks. The existing `before_clarify`
hook (git commit) still fires once before the whole command. The new `before_question` hook
fires N times (once per question). They're independent.

If oracle also has a `before_clarify` entry in the future (e.g., to surface a high-level
context summary before any questions start), that would coexist with `before_question`
per-question hooks.

---

## Files to modify

| File | Change |
|---|---|
| `speckit-clarify/SKILL.md` | Add `before_question` hook-check block at top of step 4 |
| `.specify/extensions.yml` | Add oracle `before_question` entry |

No other SpecKit files need modification. Oracle remains the owner of the extensions.yml
entries — SpecKit provides the hook surface, oracle registers on it.
