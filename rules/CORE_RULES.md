# TrekMUD Core Rules — v1.0

Status: **APPROVED BASELINE — 2026-10-06**.

These rules are the locked TrekMUD v1.0 campaign baseline. Future changes require an explicit versioned rules revision; they are never applied silently.

## Design principles

1. **Open campaign, not railroad.** The GM prepares situations and consequences, not a required sequence of player choices.
2. **Career simulation, not XP grinding.** Rank and billet are separate.
3. **Competence first.** Routine professional tasks succeed without rolls.
4. **Uncertainty is mechanical.** Genuine uncertain actions use 2d6 + attribute + skill + relevant specialty + situational modifiers.
5. **No dice fudging.** Consequential randomness comes from the auditable deterministic RNG.
6. **Information is local.** The player knows what the character can plausibly know.
7. **The ship is a living workplace.** Duty, friendships, rivalries, training, downtime and mundane routines matter alongside crises.
8. **NPCs persist.** Important crew have careers, relationships and goals independent of the player.
9. **Consequences persist.** Commendations, failures, injuries, disciplinary events and reputation affect later opportunities.
10. **Canon is a constraint, not a railroad.** Canon defines the wider setting. TrekMUD's ship and crew develop their own history.
11. **State beats memory.** Repository state and committed checkpoints are authoritative when chats disagree.

## Rules v1.0 package

- `OPEN_PLAY.md` — free-form action, non-railroad GMing, improvisation and persistent setting fill
- `ATTRIBUTES_SKILLS.md` — attributes, broad skills, specialties, qualifications and starting-Ensign baseline
- `RESOLUTION.md` — when to roll, targets, margins, assistance and extended work
- `CONSEQUENCES.md` — injury, fatigue and professional consequences
- `ADVANCEMENT.md` — skill evidence, promotion readiness, billets and transfers
- `RELATIONSHIPS.md` — player-visible relationships and persistent NPC materialization
- `RNG.md` — deterministic SHA-256 counter RNG and audit policy
- `CAREER.md` — Starfleet rank/billet structure, specialties and career progression

## Resolution summary

A trained professional with sufficient time, tools and information succeeds at routine work automatically.

When uncertainty matters:

`2d6 + Attribute + Skill + one relevant Specialty + situational modifiers`

Targets:

- 7 — pressured routine
- 9 — professional challenge
- 11 — difficult
- 13 — severe
- 15 — extraordinary

A one-point miss may become success with a meaningful cost when that makes sense; it is not guaranteed.

## Persistence

A campaign checkpoint is required after:

- major decisions
- rank/billet/qualification changes
- relationship milestones
- mission changes
- discoveries with future relevance
- injury or disciplinary events
- significant possessions/equipment changes
- session end

The player-visible state engine validates all revisioned component files as one snapshot. Checkpoints are content-hashed and immutable once committed.

## Baseline protection

Rules v1.0 is immutable as an approved baseline.

Any future mechanical change must:

1. be proposed separately from live campaign state;
2. identify the exact v1.0 behavior being changed;
3. preserve existing campaign history;
4. receive explicit approval;
5. create a new versioned rules entry rather than silently rewriting v1.0.
