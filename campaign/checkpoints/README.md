# Campaign checkpoints

A checkpoint is an immutable manifest named `rNNNNN.json`.

The manifest records:

- campaign revision
- rules version
- human summary
- previous checkpoint ID
- validation result
- SHA-256 of every player-visible state file included in the save

The Git commit that first introduces a checkpoint manifest is the authoritative repository checkpoint. User approval of a checkpoint is recorded separately and must reference that exact commit SHA.

Checkpoint files are never edited after merge. A correction creates a later revision explaining what changed.
