<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

Task-tracking state (TodoWrite/TaskList, spec checklists, in-prompt status blocks) does not auto-reconcile across context boundaries such as /compact, /clear, or resumed sessions. Tasks completed in a prior segment can persist as 'in_progress' or 'pending', creating false-unfinished signals that risk either duplicate work or false 'incomplete' status reports. Treat the state display as a hypothesis; verify against on-disk artifacts (files, grep, git) as ground truth, then update state to match before acting.
