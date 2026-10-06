# TrekMUD player-visible records

Status: **APPROVED PLAYER-STATE SCHEMA v1**

`campaign/records.json` is the structured career/history layer behind the Player Console's **Records** view.

It contains only facts Jeremy could legitimately know or observe. Hidden motives, unrevealed mission facts, secret relationship values, and future plot state remain in private TrekMUD-GM.

## Streams

### Duty Log — `DUTY-`

Player-visible duty-shift and assignment history.

Typical fields:

- `id`
- `year`
- `stardate`
- `shipTime`
- `title`
- `summary`
- `department`
- `status`
- `locationId` when useful

Routine minutes do not need an entry. Record things that would matter in a future career review or session recap.

### Science Findings — `SCI-`

Scientific observations, hypotheses, analyses, discoveries, samples, sensor findings, and formal conclusions Jeremy has participated in or learned.

Typical fields:

- `id`
- `year`
- `stardate`
- `title`
- `summary`
- `domain`
- `status` — e.g. OBSERVATION, HYPOTHESIS, CONFIRMED, REFUTED
- `confidence` when meaningful
- `locationId` or subject reference when useful

Do not put unrevealed GM answers in this stream.

### Mission Records — `MIS-`

Persistent player-visible mission history.

Typical fields:

- `id`
- `title`
- `year`
- `startStardate`
- `endStardate` or null
- `role`
- `status` — ACTIVE, COMPLETE, ABORTED, TRANSFERRED
- `outcome` when known
- `summary`
- `sourceThreadId` when the record originated from a campaign thread

A mission record is not a quest requirement. It is history.

### Relationship Milestones — `RELM-`

Observable moments in Jeremy's relationship history with a persistent NPC.

Typical fields:

- `id`
- `year`
- `stardate`
- `targetId`
- `relationshipId` when a public relationship record exists
- `title`
- `summary`
- `tone` when useful

Examples include first meaningful conversation, conflict, trust earned, apology, invitation, recommendation, or explicitly established friendship.

This stream records events, not hidden affection/trust scores.

### Ship Events — `SHIPLOG-`

Player-visible changes to USS Asteria's condition or operations.

Typical fields:

- `id`
- `year`
- `stardate`
- `shipTime`
- `shipId`
- `title`
- `summary`
- `system`
- `severity` — INFO, CAUTION, ALERT, CRITICAL
- `status`

Examples include red alert, sensor-array outage, damage, repairs, docking/undocking, or a mission-pod configuration change that Jeremy can know.

## Persistence

Records are append-oriented career history.

Corrections should be explicit. Do not silently rewrite an old record because later information changes its interpretation.

A newly learned truth may add a later Science Finding or Mission Record that says an earlier hypothesis was refuted.

## Checkpoint rule

Records are part of the same atomic campaign snapshot as character, crew, relationships, knowledge, ship state, and location state.

When a record-worthy event occurs:

1. update the relevant live state;
2. append the appropriate player-visible record(s);
3. increment all revisioned campaign components together;
4. validate campaign state;
5. create the matching `rNNNNN` checkpoint.

The record stream must never get ahead of or lag behind the checkpoint that makes the event canonical.
