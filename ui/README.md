# TrekMUD Player Console

A read-only visual companion to the chat-based RPG.

## Architecture

The console never fetches raw campaign files from the browser and never connects to `TrekMUD-GM`.

Build flow:

1. `scripts/build_player_console.py` reads approved public campaign components.
2. It selects player-visible fields and derives deterministic display coordinates for persistent ship locations.
3. It emits `_site/data/player-console.json`.
4. The static browser app reads only that generated JSON.

The UI is vanilla HTML/CSS/JavaScript with no runtime framework or third-party CDN dependency.

## Views

- Right Now
- Ship Map
- Character
- Crew
- Threads
- Timeline

The map uses stable campaign location IDs. Visual coordinates are presentation data derived deterministically from each ID; they do not modify canonical ship topology.

## Validation

`scripts/validate_player_console.py` verifies:

- checkpoint/revision alignment;
- 131 locations / 138 connections / 19 decks;
- 500-person crew totals and 20 materialized identities;
- organic character values remain unresolved where appropriate;
- no private GM repository/file identifiers enter the browser artifact;
- no RNG seed or public commitment enters the console.

## GitHub Pages

Deployment is defined in `.github/workflows/deploy-player-console.yml`.

One-time repository setup:

1. Open **Settings → Pages**.
2. Under **Build and deployment**, select **GitHub Actions** as the source.
3. Run the **Deploy TrekMUD player console** workflow once.

The initial deployment workflow is manual-only so a disabled Pages setting cannot make ordinary `main` builds fail.

After the first verified deployment, automatic deployment on validated campaign updates can be enabled safely.
