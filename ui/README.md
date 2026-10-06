# TrekMUD Player Console

A read-only visual companion to the chat-based TrekMUD campaign.

## Current experience

The console is designed as Jeremy Hennessy's Starfleet PADD rather than a game-control panel.

Views:

- **Right Now** — current assignment, exact location, next obligation, Science context, known facts
- **Ship** — Nebula-class vessel profile, command staff, mission pod, reported condition, quick destinations
- **Ship Map** — 28-deck cutaway, P1-P4 sensor-pod levels, searchable compartments, access-aware routing
- **Character** — organic attributes, skills, qualifications and still-unresolved discovery pools
- **Crew** — searchable player-visible directory with department identity
- **Threads** — known obligations and schedule
- **Records** — five structured player-visible history streams with filters and counts
- **Timeline** — combined service/discovery/record history

## Architecture

The browser never connects to `TrekMUD-GM`.

Build flow:

1. `scripts/build_player_console.py` reads approved public campaign components.
2. `scripts/build_map_layout.py` derives presentation-only Nebula-class deck/pod layouts from stable location IDs.
3. The builder emits `_site/data/player-console.json`.
4. The static browser app reads only that generated player-safe snapshot.

The UI uses vanilla HTML/CSS/JavaScript with no runtime framework or third-party CDN dependency.

## Map and routing

Canonical geography remains `campaign/locations.json`.

The PADD presents that graph as:

- a clickable 28-deck ship cutaway;
- four selectable dorsal sensor/science-pod levels;
- compartment-block deck plans;
- department and restricted-access coding;
- a persistent YOU ARE HERE marker;
- room search across the ship directory;
- standard-access shortest-path guidance from Jeremy's current location;
- quick routes to quarters, Science, Sickbay and the mess.

Standard routing deliberately excludes restricted rooms and restricted graph edges. A restricted compartment can still appear in the directory but the ordinary PADD route planner will not claim Jeremy has access.

Visual deck placement is presentation-only and never mutates campaign topology.

## Mobile / standalone mode

The console includes an app manifest plus Apple standalone metadata.

On narrow screens the desktop rail becomes a bottom PADD navigation bar, with safe-area padding for modern iPhones.

Browser URL hashes preserve the selected view so back/forward navigation works naturally.

## Validation

`scripts/validate_player_console.py` verifies:

- checkpoint/revision alignment;
- USS Asteria / Nebula-class identity;
- official/reference ship profile values exposed to the PADD;
- 200 locations / 206 connections / 28 decks / P1-P4;
- 750-person complement including Jeremy;
- 20 materialized NPCs + 729 background crew;
- organic character values remain unresolved where appropriate;
- standard-access paths exist to all quick-route destinations;
- no private GM repository/file identifiers enter the browser artifact;
- no RNG seed or public commitment enters the console;
- standalone web-app packaging is complete.

## GitHub Pages

`.github/workflows/deploy-player-console.yml` automatically validates and redeploys the console after relevant `main` changes.

The deployment job runs campaign, USS Asteria baseline, and player-console validation before publication.

Current campaign target: **r00004 · revision 4 · USS Asteria · 1217 hours · RNG counter 0**. The five Records streams are initialized and intentionally empty before Scene One.
