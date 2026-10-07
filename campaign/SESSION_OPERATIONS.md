# TrekMUD session operations

Status: **PRE-SESSION OPERATING PROCEDURE v1**

This document describes the safe workflow for actually playing TrekMUD from chat.

## Before a session

Run:

`python scripts/session_preflight.py`

The preflight must succeed before narration begins.

It verifies:

- campaign-state coherence;
- the active checkpoint manifest exists;
- every file hashed by the active checkpoint still matches its saved SHA-256 value;
- the previous checkpoint manifest still exists;
- USS Asteria topology and crew baselines validate;
- the player-safe PADD snapshot agrees with the campaign state;
- current location and RNG counter agree across the resume packet and UI snapshot.

A compact cross-chat packet can be generated with:

`python scripts/build_resume_packet.py --write-json /tmp/trekmud-resume.json --write-md /tmp/trekmud-resume.md`

## Scene One

The first narrated action starts from the exact canonical state:

- checkpoint `r00005`;
- revision 5;
- 2372;
- Stardate 49317.4;
- ship time 12:17;
- USS Asteria at Starbase 375;
- Jeremy in Transporter Room 2;
- campaign status `READY_TO_START`;
- RNG counter 0.

No real-world time passes in-game merely because the chat resumes tomorrow.

## Basic scene-state changes

Use `scripts/apply_scene_state.py` for ordinary visible scene bookkeeping:

- activate the campaign;
- advance ship time within the current ship day;
- move Jeremy to another non-restricted mapped location;
- mark known calendar entries with a new status.

The input is a JSON object.

Example:

```json
{
  "summary": "Jeremy leaves Transporter Room 2 after checking in.",
  "activateCampaign": true,
  "advanceMinutes": 5,
  "locationId": "AST-D09-HUB-C",
  "calendarStatusUpdates": []
}
```

The tool increments every revisioned campaign component together and validates the result.

It does **not** create the checkpoint itself.

Afterward:

`python scripts/create_checkpoint.py --summary "<what changed>"`

Then run:

`python scripts/session_preflight.py`

before calling the save canonical.

## Specialized state changes

Use the specialized transactions when their subject actually occurs:

- `apply_character_discovery.py` — organic attribute/skill/specialty/background discoveries;
- `apply_player_records.py` — Duty, Science, Mission, Relationship Milestone, and Ship Event records.

Do not create a character discovery or record just because a scene happened. Persist only material facts that were actually established.

## Randomness

The private RNG seed remains in TrekMUD-GM.

Public campaign state stores only the algorithm, commitment, and consumed counter.

Whenever a roll is needed:

1. identify the check and stakes before rolling;
2. use the private deterministic RNG;
3. advance the public and private counters consistently;
4. include the resulting state in the next checkpoint.

Never regenerate a roll because the outcome was inconvenient.

## Save cadence

Checkpoint after:

- a meaningful player decision;
- time/location changes that matter;
- a character discovery;
- relationship or knowledge changes;
- an important scientific finding;
- mission/thread changes;
- ship-state changes;
- the end of a play session.

Tiny conversational exchanges do not require one Git commit each. Several immediately related events may be saved together when they form one coherent state transition.

## Failure recovery

If any transaction or validation fails:

- stop advancing narration;
- treat the previous validated checkpoint as authoritative;
- inspect the smallest inconsistent layer;
- repair it;
- rerun validation;
- only then continue play.

Never patch the repository to match remembered narration without making the correction explicit.

## Tomorrow-ready state

The current intended starting point is `r00005`.

Revision 5 is a zero-time continuity cleanup over r00004:

- onboarding thread correctly names USS Asteria;
- no time passed;
- no RNG was consumed;
- no record streams were populated;
- no hidden story state was generated.
