# TrekMUD Core Rules — draft v0.9

Status: **pre-campaign draft**. Nothing here is v1.0/locked until explicitly approved.

## Design principles

1. **Career simulation, not XP grinding.** Rank and billet are separate.
2. **Competence first.** Routine professional tasks succeed without rolls.
3. **Uncertainty is mechanical.** Genuine uncertain actions use a lightweight 2d6 + attribute + skill + situational modifier check.
4. **No dice fudging.** Random outcomes are reproducible from persisted RNG state once the campaign begins.
5. **Information is local.** The player knows what the character can plausibly know.
6. **The ship is a living workplace.** Duty, friendships, rivalries, training, downtime and mundane routines matter alongside crises.
7. **NPCs persist.** Important crew have careers, relationships and goals independent of the player.
8. **Consequences persist.** Commendations, failures, injuries, disciplinary events and reputation affect later opportunities.
9. **Canon is a constraint, not a railroad.** Canon defines the wider setting. TrekMUD's ship and crew develop their own history.
10. **State beats memory.** Repository state and committed checkpoints are authoritative when chats disagree.

## Resolution ladder

Typical uncertain action:

`2d6 + attribute + skill + situational modifiers`

Outcomes are interpreted as:

- exceptional success
- success
- success with complication/cost
- failure
- severe failure

Exact thresholds and attribute/skill ranges remain to be finalized before v1.0.

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

Approved checkpoints are append-only history. Corrections create a new revision explaining the correction rather than silently rewriting the past.
