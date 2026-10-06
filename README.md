# TrekMUD

A persistent, text-first Star Trek career/life RPG set aboard **USS Meridian, NCC-63542**, an Akira-class Starfleet vessel in 2372.

TrekMUD is designed to play like an open tabletop campaign rather than a branching story: the player can attempt unplanned actions, pursue side threads, change career direction, build relationships, fail, improvise and create lasting consequences.

## Current campaign status

**Pre-character checkpoint: `r00000`**

- Campaign status: **NOT_STARTED**
- Rules: **v1.0**
- In-universe year: **2372**
- Stardate: **49317.4**
- Ship time: **12:17**
- Ship location: **Starbase 375**
- Opening arrival: **Transporter Room 2**
- Assigned quarters after character creation: **Deck 7, Section 12, 0712-C**
- Player character: **not yet created**
- USS Meridian map: **131 persistent locations / 138 connections**
- Crew model: **500 total; 20 persistent starting identities; 480 background crew**
- Structured lore baseline: **41,388 STAPI records**
- TNG/DS9 era index: **349 full episodes / 1,350 linked characters**

The next canonical campaign revision is character creation, which will produce **revision 1 / r00001**. No narrative action has occurred yet.

## Approved baselines

Exact approved commits are recorded in `baselines/`.

Major baselines include:

- persistent campaign state engine v1
- Rules v1.0
- USS Meridian topology v1.0
- structured lore v1.0
- USS Meridian crew structure v1.0
- pre-character checkpoint `r00000`

Approved history is never silently rewritten. Future work builds forward.

## Repository role

This repository is the durable player-visible source of truth. Chat is the play interface; Git is the continuity ledger.

```
baselines/     exact approved project/campaign baselines
rules/         locked game mechanics and open-play rules
campaign/      current player-visible state, chronicle and checkpoints
world/         USS Meridian topology, crew structure and other setting state
lore/          canon/source/provenance and 2372 knowledge policy
data/stapi/    generated structured Star Trek reference snapshot
scripts/       state, checkpoint, RNG, lore and character tooling
tests/         non-canonical validation fixtures
gm-template/   schema/protocol only for future private GM storage
```

For cross-chat continuation, follow `campaign/RESUME_PROTOCOL.md`.

## Campaign principles

- The player begins as a low-ranking **Starfleet Ensign**.
- Rank and billet are separate.
- Advancement follows demonstrated service, competence, conduct and opportunity rather than XP.
- Routine professional work normally succeeds without dice.
- Consequential uncertainty uses the locked 2d6 Rules v1.0 system.
- NPCs and improvised world details persist once they matter.
- Canon constrains the wider setting but does not railroad the player's local story.
- Player knowledge is distinct from what exists in the lore database.
- Real-world time passing does not advance campaign time.

## Lore

The first structured ingestion layer is [STAPI](https://stapi.co/).

The verified baseline contains **41,388 reusable structured records** with zero ingestion failures. Trading-card resource families are intentionally excluded under the source/licensing policy.

See:

- `lore/SOURCES.md`
- `lore/SOURCE_REGISTRY.md`
- `lore/CANON_POLICY.md`
- `lore/ERA_2372.md`

TrekMUD stores structured facts, source references and original summaries. It does not mirror episode scripts, subtitles or copyrighted encyclopedia prose.

## Character creation

Character creation is implemented and validated in `scripts/create_character.py`.

The player chooses identity, species, department, specialties, attributes and background. The tool then creates all revision-1 campaign state atomically and a validated `r00001` checkpoint is made before Scene One.

See `campaign/CHARACTER_CREATION.md`.

## Private GM-state requirement

This repository is currently public.

Do **not** commit hidden NPC motives, mystery answers, secret relationship state, future plot clocks or the deterministic RNG secret seed here.

Before live narrative play begins, either:

1. make TrekMUD private; or
2. create a private companion store/repository such as `TrekMUD-GM`.

The public campaign files remain the player-visible truth either way.
