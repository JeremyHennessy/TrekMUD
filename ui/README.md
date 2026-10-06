# TrekMUD Player Console

A read-only visual companion to the chat-based RPG.

## Architecture

The console never fetches private GM state and never connects to `TrekMUD-GM`.

Build flow:

1. `scripts/build_player_console.py` reads approved public campaign components.
2. `scripts/build_map_layout.py` derives presentation-only Nebula-class deck/pod layouts from stable campaign location IDs.
3. The builder emits `_site/data/player-console.json`.
4. The static browser app reads only that generated JSON.

The UI uses vanilla HTML/CSS/JavaScript with no runtime framework or third-party CDN dependency.

## Map

The Asteria map has two coordinated layers:

- **ship cutaway** — all 28 numbered decks plus P1–P4 science-pod levels;
- **selected plan** — compartment blocks, central circulation, access state, department coding, connections and Jeremy's current-location marker.

Canonical geography remains `campaign/locations.json`. The visual layout is presentation-only and never changes topology.

## Validation

`scripts/validate_player_console.py` verifies:

- checkpoint/revision alignment;
- USS Asteria / Nebula-class identity;
- 200 locations / 206 connections / 28 decks / four pod levels;
- 750-person complement including Jeremy;
- 20 materialized NPC identities + 729 background crew;
- organic character values remain unresolved where appropriate;
- no private GM repository/file identifiers enter the browser artifact;
- no RNG seed or public commitment enters the console.

## GitHub Pages

`.github/workflows/deploy-player-console.yml` automatically rebuilds and deploys the console after relevant validated `main` changes.

The deploy job runs campaign, Asteria-baseline, and player-console validation before publishing.

## Current deployment baseline

The current console target is public checkpoint `r00003` on USS Asteria. A merge touching `ui/**`, `campaign/**`, or the Asteria console build files automatically validates and redeploys GitHub Pages.
