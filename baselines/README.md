# TrekMUD approved baselines

This directory records exact Git commits that define approved, immutable project baselines.

A baseline manifest does not mean the repository can never evolve. It means future changes must build forward from the recorded state rather than silently rewriting what was approved.

Approved baseline commits:

- persistent campaign state engine v1 — `f96ccdee9dcbd096b42c187539efaf71fbbed914`
- Rules v1.0 — `d0feb35647e2a9dc43aa19f8930f709a4fd61b5b`
- USS Meridian topology v1.0 — `bf9b0f0b94e4853d471b178d6ad8fb0e50d625a9`

- Star Trek structured lore baseline v1 — `584e27b794c0a4c82d06d580621fd93c632fe312`
- USS Meridian crew structure v1.0 — `4fd20fd79c493735199fd1c8513fd8b0560fca32`

- Pre-character campaign checkpoint r00000 — `bd101d37897c208c8b4654461eb96ffc59cc8bcd`\n\nCharacter creation will produce revision 1 / r00001 without rewriting r00000.
