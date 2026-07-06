# Team Decision Oracle

This repo IS the oracle — records in `records/`, retrieval index in `INDEX.md`.

- Before recommending an architectural approach, technology choice, or tradeoff
  in any session, run `/oracle "[question]"` first. Empty results are a valid
  signal, not a failure.
- Records are immutable once merged. Corrections are new records that supersede
  old ones (update the old record's Status line only).
- Every PR that adds or changes a record must update its line in `INDEX.md`.
- Never write files into `inbox/` except via the miner; never commit `inbox/`.
- ID allocation: take the highest existing ID across local files AND
  `git show origin/main:INDEX.md`, then +1. Merge conflicts on INDEX.md
  arbitrate races — renumber the unmerged side.
