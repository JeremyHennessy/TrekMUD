# Private GM storage protocol

Status: **OPERATING PROCEDURE v1.0**

## Before Scene One

Live narrative play should not begin until a private GM store exists.

At initialization:

1. start from public checkpoint `r00001` after character creation;
2. create the private state at the same campaign revision;
3. generate a cryptographically random 32-byte RNG seed privately;
4. store the seed only in private GM state;
5. publish only SHA-256(seed) into `campaign/rng.json`;
6. verify public and private counters both begin at 0;
7. checkpoint the public state again if the public RNG commitment changed.

## During play

Private GM state tracks only facts that should remain hidden.

Player-visible consequences must migrate into the public campaign state when the character observes or learns them.

Examples:

- NPC secretly dislikes the player → private;
- NPC openly argues with the player → public relationship/history;
- hidden saboteur identity → private;
- player discovers saboteur identity → public knowledge;
- future event clock → private;
- red alert triggered by that event → public ship state.

## Save atomicity

A complete session save consists of:

- one validated public campaign checkpoint; and
- one private GM-state revision pointing to that checkpoint.

Do not knowingly continue play with one side saved and the other side stale.

## Cross-chat resume

A future GM first loads the public checkpoint per `campaign/RESUME_PROTOCOL.md`, then loads the private state with the matching revision/checkpoint.

Hidden files are never summarized back to the player unless the character has learned the information in play.
