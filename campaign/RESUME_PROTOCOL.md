# TrekMUD cross-chat resume protocol

Status: **APPROVED OPERATING PROCEDURE v1.0**

The repository, not conversational memory, is the continuity authority.

A new chat must be able to resume TrekMUD without asking the player to reconstruct previous events.

## When the player says "continue TrekMUD"

Before narrating anything:

1. Read the current `main` branch head.
2. Read `campaign/state.json`.
3. Read the checkpoint identified by `state.checkpoint.lastCheckpointId`.
4. Confirm the checkpoint revision matches `state.revision`.
5. Read `campaign/config.json` and the component files listed in `state.components`.
6. Read the relevant recent section of `campaign/CHRONICLE.md`.
7. Read `rules/CORE_RULES.md` for the rules version named by state.
8. Load only the crew, locations, relationships, knowledge and active threads needed for the current scene, expanding as required.
9. If private GM storage exists, load the matching hidden-state revision separately. Never infer hidden state from player-visible files.
10. Continue from the exact saved in-universe time and location unless the player explicitly requests a time skip.

Do **not** ask the player for a recap merely because the conversation changed.

## Authority order

If chat text and repository state conflict:

1. latest valid campaign checkpoint;
2. approved baseline manifests;
3. append-only chronicle;
4. current-scene facts not yet checkpointed;
5. conversational recollection.

Never silently rewrite a validated checkpoint to match a remembered version.

## Before each scene

Confirm internally:

- current revision;
- current stardate/year/ship time;
- player location;
- ship location and alert state;
- active duty/calendar obligations;
- relevant injuries/fatigue;
- relevant known relationships;
- active threads;
- what the player character actually knows.

The lore database can contain facts the player does not know. `campaign/knowledge.json` is the player-knowledge gate.

## Open-play adjudication

The player can attempt actions that were never anticipated.

When improvisation creates a materially important new:

- NPC;
- room/location;
- item;
- relationship;
- fact;
- obligation;
- investigation thread;

give it a stable ID and persist it at the next checkpoint.

Do not regenerate established details for convenience.

## Saving after play

A save-worthy change includes:

- meaningful player decision;
- new or changed relationship;
- newly materialized NPC;
- mission/thread change;
- important discovery;
- injury/fatigue change;
- inventory change;
- qualification/career change;
- location/time advancement that matters;
- end of a play session.

For a new revision:

1. increment the root revision;
2. set every revisioned component to the same revision;
3. update all affected state files;
4. append material history to `CHRONICLE.md`;
5. run `scripts/validate_campaign.py`;
6. run `scripts/create_checkpoint.py`;
7. commit the coherent state and checkpoint together;
8. verify CI on the exact commit before calling the save canonical.

Checkpoint IDs are `rNNNNN`, matching the campaign revision.

## Failure recovery

If a write or validation fails:

- do not partially advance the story;
- the previous validated checkpoint remains authoritative;
- inspect the diff against that checkpoint;
- repair the smallest inconsistent layer;
- rerun validation before continuing.

## Time between chats

Game time does not pass simply because real-world time passes.

The campaign clock advances only through narrated play or an explicit player-approved time skip.

## Hidden GM state

The public TrekMUD repository must never contain:

- NPC secret motives;
- unrevealed loyalties;
- hidden relationship values;
- mystery solutions;
- future plot clocks;
- secret RNG seed;
- unrevealed mission outcomes.

Before live play uses those systems, store them in a private repository/store synchronized to the public campaign revision.

## Current handoff point

At pre-character checkpoint `r00000`:

- campaign revision: 0
- status: `NOT_STARTED`
- rules: v1.0
- year: 2372
- stardate: 49317.4
- ship time: 12:17
- ship: USS Meridian, NCC-63542, Akira-class
- ship location: Starbase 375
- opening arrival: Transporter Room 2 (`MER-D09-TR-02`)
- assigned quarters after character creation: `MER-D07-S12-0712C`
- player character: not yet created
- RNG: uninitialized
