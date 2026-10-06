# TrekMUD Maps

Maps in TrekMUD are **game-state topology first** and artwork second.

The authoritative representation of a location should be structured data describing rooms/areas and their connections. Rendered diagrams can then be regenerated without changing gameplay geography.

## USS Meridian map plan

The Meridian will receive an original deck graph constrained by known Akira-class/canon-era ship functions without copying third-party blueprint artwork.

Each room/area should eventually have:

- stable location ID
- deck
- section
- display name
- location type
- access restrictions
- adjacent location IDs
- turbolift/jefferies-tube connectivity
- department ownership
- public/crew/restricted status
- discovered-by-player state
- optional damage/environment state

Example ID pattern:

`MER-D07-S12-0712C`

The first approved ship layout becomes a locked geography baseline. Later story damage or refits are recorded as state changes rather than silently moving rooms.

## External maps

Official/fan deck plans may be used as research references when legally accessible. Do not commit scans or copied artwork without a compatible license and attribution.
