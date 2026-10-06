# TrekMUD campaign state schema — v1.0

Status: **APPROVED BASELINE**\n\nThis directory is the durable player-visible state of the campaign.

## Authority and atomicity

A valid campaign checkpoint is one Git commit containing a mutually consistent set of campaign files. A change is not a checkpoint merely because one JSON file was edited.

Before a checkpoint is accepted:

1. all campaign JSON must parse;
2. `scripts/validate_campaign.py` must pass;
3. the revision number must agree across revisioned state files;
4. references must resolve;
5. the new checkpoint manifest must describe the files that changed;
6. the chronicle entry must agree with the state transition for material events.

If validation fails, the previous committed checkpoint remains authoritative.

## Core files

- `state.json` — root snapshot and references to all component files
- `character.json` — player character identity and current personal state
- `service-record.json` — career history, promotions, evaluations, commendations and discipline
- `qualifications.json` — formal skills/qualifications/certifications
- `inventory.json` — persistent possessions and issued equipment
- `crew.json` — named crew the campaign has materialized
- `relationships.json` — persistent player-visible relationship state
- `knowledge.json` — facts the player character actually knows
- `active-threads.json` — unresolved player-visible story/career threads
- `calendar.json` — scheduled duties, appointments and known future commitments
- `ship.json` — current player-visible state of USS Meridian
- `locations.json` — authoritative ship/location topology visible to the campaign
- `rng.json` — deterministic RNG metadata; secret seed is not stored while the repository is public
- `checkpoints/` — immutable checkpoint manifests

## Revisions

Revision 0 is the validated pre-character state preserved as checkpoint `r00000`.

The first played scene may only begin after:

- rules v1.0 is approved;
- character creation is complete;
- a valid revision 1 checkpoint is committed.

Revision numbers are monotonically increasing integers. Never reuse a revision number.

## IDs

IDs are stable and never repurposed.

Suggested prefixes:

- `PC-` player character
- `CREW-` named crew
- `REL-` relationship
- `KN-` knowledge fact
- `TH-` active thread
- `QUAL-` qualification
- `ITEM-` item
- `MER-` USS Meridian locations

## NPC materialization tiers

- Tier 1 — core persistent NPC: full personal/career/relationship state
- Tier 2 — persistent named crew: stable identity, rank, department, billet and lighter state
- Tier 3 — background population: represented statistically until meaningful interaction materializes a stable named record

Once a Tier-3 person is materialized into Tier 1 or 2, their identity is persistent and must not be regenerated.

## Hidden state

This public repository must not contain unrevealed GM secrets. Hidden state will require either a private repository or a separate private store. Player-visible state must never infer hidden facts merely because the lore database contains them.
