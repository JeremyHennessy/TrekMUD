# TrekMUD Core Rules — proposed v1.0

Status: **UNAPPROVED PROPOSAL**.

This branch is the candidate rules package for the campaign. Nothing becomes locked Rules v1.0 until Jeremy explicitly approves the package.

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

## Proposed v1.0 package

- `OPEN_PLAY.md` — free-form action, non-railroad GMing, improvisation and persistent setting fill
- `ATTRIBUTES_SKILLS.md` — attributes, broad skills, specialties, qualifications and starting-Ensign baseline
- `RESOLUTION.md` — when to roll, targets, margins, assistance and extended work
- `CONSEQUENCES.md` — injury, fatigue and professional consequences
- `ADVANCEMENT.md` — skill evidence, promotion readiness, billets and transfers
- `RELATIONSHIPS.md` — player-visible relationships and persistent NPC materialization
- `RNG.md` — deterministic SHA-256 counter RNG and audit policy
- `CAREER.md` — Starfleet rank/billet structure already established in draft v0.9

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

## Locking procedure

When the rules are approved:

1. record the exact approved commit SHA;
2. change the package status from proposal to approved;
3. set campaign `rulesVersion` to `1.0`;
4. create a rules changelog entry;
5. never alter v1.0 silently—future changes become explicit versioned revisions.
