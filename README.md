# TrekMUD

A persistent, open-ended Star Trek career/life RPG aboard **USS Meridian, NCC-63542**, an Akira-class Starfleet vessel in 2372.

Chat is the tabletop. Git is the continuity ledger. The Player Console is the visual PADD.

## Current campaign status

**Checkpoint: `r00002` · Revision 2 · READY_TO_START**

- Player: **Ensign Jeremy Hennessy**
- Species: Human · age 30 · he/him
- Upbringing: Federation starbase; exact station intentionally unresolved
- Department: **Science**
- Billet: Junior Science Officer
- Rules: **v1.1 Organic Character Discovery**
- Stardate: **49317.4**
- Ship time: **12:17**
- Ship location: **Starbase 375**
- Jeremy's location: **Transporter Room 2**
- Assigned quarters: Deck 7, Section 12, 0712-C
- USS Meridian map: **131 persistent locations / 138 connections**
- Crew model: **500 total; 20 persistent identities; 480 background crew**
- Lore baseline: **41,388 STAPI records**
- TNG/DS9 era index: **349 full episodes / 1,350 linked characters**
- Deterministic RNG: initialized, counter **0**
- Narrative actions taken: **0**

The private companion repository `JeremyHennessy/TrekMUD-GM` is synchronized to `r00002` and contains the secret RNG seed plus future GM-only state. No hidden plot, mystery, relationship, or off-screen event state was prewritten at initialization.

## Player Console

`ui/` contains a read-only player-facing campaign console.

Views:

- **Right Now** — location, time, ship state, obligations, active threads
- **Ship Map** — interactive deck schematic generated from persistent location IDs
- **Character** — organic attributes/skills and remaining discovery pools
- **Crew** — searchable player-visible crew directory
- **Threads** — known obligations, schedule, and open campaign threads
- **Timeline** — persistent service and character-discovery history

The browser never reads `TrekMUD-GM`. `scripts/build_player_console.py` generates a compact player-safe JSON snapshot from public campaign files only, and `scripts/validate_player_console.py` rejects private-state markers or RNG commitment leakage.

The console is prepared for GitHub Pages via `.github/workflows/deploy-player-console.yml`.

## Repository role

```
baselines/     exact approved project/campaign baselines
rules/         versioned game mechanics and open-play rules
campaign/      current player-visible state, chronicle and checkpoints
world/         USS Meridian topology and crew structure
lore/          canon/source/provenance and 2372 knowledge policy
data/stapi/    structured Star Trek reference snapshot
ui/            player-facing campaign console
scripts/       state, checkpoint, RNG, lore, character and UI tooling
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

## Lore and attribution

The primary structured ingestion layer is [STAPI](https://stapi.co/). The verified baseline contains **41,388 reusable structured records** with zero ingestion failures. Trading-card resource families are intentionally excluded.

See:

- `lore/SOURCES.md`
- `lore/SOURCE_REGISTRY.md`
- `lore/CANON_POLICY.md`
- `lore/ERA_2372.md`

TrekMUD stores structured facts, source references and original summaries. It does not mirror episode scripts, subtitles or copyrighted encyclopedia prose.

## Security boundary

Public TrekMUD contains only player-visible state.

Private material—including unrevealed NPC motives, mystery answers, secret relationship state, future plot clocks and the RNG seed—belongs only in the private `TrekMUD-GM` repository. Public/private revisions must remain synchronized before play continues.
