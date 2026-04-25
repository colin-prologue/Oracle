# scripts/

## test-hooks.py

Hook-firing test harness for Claude Code settings.

### Why

PHI-004 (validate safety nets against actual workflow) names a revisit trigger:
when test harnesses can replay real workflows and assert which hooks fired,
manual trace validation becomes automatable. This script is that harness.

### Usage

Run against your real config:

```
python3 scripts/test-hooks.py --settings ~/.claude/settings.json --settings .claude/settings.json
```

Run with no flags to use the default pair (`~/.claude/settings.json`,
`.claude/settings.json`).

### Assertions

Place a sidecar file next to any `settings.json` named
`settings.assertions.json` to declare expected outcomes:

```json
[
  {
    "event": "PreToolUse",
    "matcher": "Bash",
    "command_contains": "block-main-commit.sh",
    "expect": "allow",
    "stdin_overrides": {"tool_input": {"command": "ls"}}
  }
]
```

`expect` is `allow` or `deny`. `stdin_overrides` is shallow-merged into the
default synthesized payload for the (event, matcher) pair. `match_assertion`
returns the first matching entry — for multi-case scenarios on the same hook,
run the harness multiple times with different override sets, or extend the
matcher (YAGNI until needed).

### Tests

```
python3 -m unittest tests.test_hooks_harness -v
```

### Limitations

- Non-command hooks (`prompt`, `agent`, `http`) are reported as SKIP.
- Default payloads are minimal; some hooks may fail because the synthesized
  payload doesn't match what the hook expects in production. Failures here
  are signal: either fix the hook to handle minimal input, or extend
  `DEFAULT_PAYLOADS` in `test-hooks.py`.
