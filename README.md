# TrekMUD

A persistent, text-first Star Trek career/life RPG set aboard a Starfleet starship during the late **The Next Generation / Deep Space Nine** era.

## Campaign baseline

- In-universe start: **2372**, stardate **49317.4**.
- Player starts as a low-ranking **Starfleet Ensign** and chooses a primary and secondary specialty.
- Rank, billet, qualifications, relationships, possessions, reputation, ship state and campaign history persist between chats.
- Primary era anchors: **Star Trek: The Next Generation** and **Star Trek: Deep Space Nine**. Earlier canon is historical background. Contemporary Voyager events exist in canon but are not automatically known to the player. Future canon is GM-only until the campaign clock reaches it.
- The player is not guaranteed command progression or protagonist status; advancement follows service, competence, conduct, opportunity and consequences.

## Repository role

This repository is the durable source of truth for rules, campaign state, world structure, maps and canon reference data. Chat is the play interface; Git is the continuity ledger.

```
rules/        approved mechanics and canon policy
campaign/     player-visible campaign state and chronicle
lore/         source/provenance and era design
scripts/      reproducible lore ingestion
data/stapi/   generated STAPI catalogue + manifests
```

> **Spoiler/security note:** this repository is currently public. Hidden GM state, NPC secrets and unrevealed plot clocks must not be committed here unless the repository is made private or a separate private store is used.

## Lore ingestion

The first ingestion layer is [STAPI](https://stapi.co/), a public Star Trek API. The updater discovers STAPI REST resources, downloads reusable structured catalogue data, records provenance and builds TNG/DS9-era episode/character indexes. It intentionally does **not** copy encyclopedia article prose, scripts, subtitles or copyrighted trading-card datasets.

See `lore/SOURCES.md` and `lore/CANON_POLICY.md` before adding data.
