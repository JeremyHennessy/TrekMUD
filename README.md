# TrekMUD

A persistent, open-ended Star Trek career/life RPG aboard **USS Asteria, NCC-63542**, a Nebula-class Starfleet vessel in 2372.

Chat is the tabletop. Git is the continuity ledger. The Player Console is the visual PADD.

## Current campaign status

**Checkpoint: `r00004` · Revision 4 · READY_TO_START**

- Player: **Ensign Jeremy Hennessy**
- Species: Human · age 30 · he/him
- Upbringing: Federation starbase; exact station intentionally unresolved
- Department: **Science**
- Billet: Junior Science Officer
- Rules: **v1.1 Organic Character Discovery**
- Stardate: **49317.4**
- Ship time: **12:17**
- Ship location: **Starbase 375**
- Jeremy's location: **Transporter Room 2 · Deck 9**
- Assigned quarters: **Deck 7 · Section 12 · 0712-C**
- USS Asteria map: **200 persistent locations / 206 connections**
- Ship structure: **28 numbered decks + P1–P4 science/sensor pod**
- Crew model: **750 total including Jeremy; 20 persistent NPCs; 729 background crew**
- Lore baseline: **41,388 STAPI records**
- TNG/DS9 era index: **349 full episodes / 1,350 linked characters**
- Deterministic RNG: initialized, counter **0**
- Player-visible career record streams: **5 initialized / 0 entries**
- Narrative actions taken: **0**

The move from USS Meridian / Akira-class to USS Asteria / Nebula-class is an approved **pre-play baseline correction**, not an in-universe rename, refit, or transfer.

The private companion repository `JeremyHennessy/TrekMUD-GM` is synchronized to the same public checkpoint before play continues. Hidden plot/mystery/relationship state remains empty until open play creates a reason for it.

## Player Console

`ui/` contains the read-only player-facing campaign console.

Views:

- **Right Now** — current assignment, location, ship state, obligations, department context
- **Ship Map** — Nebula-class deck cutaway + selectable deck plans + science-pod levels
- **Character** — organic attributes/skills and remaining discovery pools
- **Crew** — searchable player-visible crew directory with department identity
- **Threads** — known obligations, schedule, and open campaign threads
- **Records** — Duty, Science, Mission, Relationship, and Ship Event history
- **Timeline** — combined service, discovery, and record history

The browser never reads `TrekMUD-GM`. `scripts/build_player_console.py` emits player-safe state only, while `scripts/validate_player_console.py` rejects private-state markers or RNG commitment leakage.

GitHub Pages deployment is automatic on validated `main` changes through `.github/workflows/deploy-player-console.yml`.

## Repository role

```
baselines/     exact approved project/campaign baselines
rules/         versioned game mechanics and open-play rules
campaign/      current player-visible state, chronicle and checkpoints
world/asteria/ current USS Asteria topology and crew structure
world/meridian/ historical pre-play Meridian baseline
lore/          canon/source/provenance and 2372 knowledge policy
data/stapi/    structured Star Trek reference snapshot
ui/            player-facing campaign console
scripts/       state, checkpoint, RNG, lore, world, character and UI tooling
tests/         non-canonical validation fixtures
gm-template/   protocol/template for private GM storage
```

For cross-chat continuation, follow `campaign/RESUME_PROTOCOL.md`.

## Campaign principles

- The player can attempt anything plausible in the fiction; there is no required plot path.
- Rank and billet are separate.
- Advancement follows service, competence, conduct, qualifications and opportunity rather than XP.
- Routine professional work normally succeeds without dice.
- Consequential uncertainty uses the locked 2d6 system and auditable deterministic RNG.
- NPCs and improvised world details persist once they matter.
- Canon constrains the wider setting without railroading the player's local story.
- Player knowledge is distinct from what exists in the lore database.
- Real-world time passing does not advance campaign time.
- Organic character values remain unresolved until play establishes them; unresolved never means zero.

## Nebula-class source policy

Canon/reference constraints and TrekMUD setting fill are kept separate.

Canon/reference-backed constraints include:

- Nebula-class hull and late-24th-century service;
- multi-mission / science-heavy role;
- configurable dorsal pod;
- approximately 442 m length;
- large technical-reference crew complement.

TrekMUD-original setting fill includes:

- USS Asteria name and NCC-63542 registry;
- 28 numbered decks;
- exact internal room/deck distribution;
- four-level triangular long-range science/sensor pod arrangement.

See `world/asteria/SPECS.json` and `world/asteria/TOPOLOGY.md`.

## Security boundary

Public TrekMUD contains only player-visible state.

Private material—including unrevealed NPC motives, mystery answers, secret relationship state, future plot clocks and the RNG seed—belongs only in the private `TrekMUD-GM` repository. Public/private revisions must match before play continues.
