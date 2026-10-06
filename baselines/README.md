# TrekMUD approved baselines

This directory records exact Git commits that define approved, immutable project baselines.

A baseline manifest does not mean the repository can never evolve. It means future changes must build forward from the recorded state rather than silently rewriting what was approved.

Approved baseline commits:

- persistent campaign state engine v1 — `f96ccdee9dcbd096b42c187539efaf71fbbed914`
- Rules v1.0 — `d0feb35647e2a9dc43aa19f8930f709a4fd61b5b`
- USS Meridian topology v1.0 — `bf9b0f0b94e4853d471b178d6ad8fb0e50d625a9`

Additional baselines, such as lore and initial campaign checkpoint, are recorded separately once merged and validated.
