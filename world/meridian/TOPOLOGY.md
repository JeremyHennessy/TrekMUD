# USS Meridian topology — candidate baseline

Status: **CANDIDATE / UNAPPROVED**.

This is an original TrekMUD ship layout. It uses canon/reference constraints for the Akira class but does not copy third-party deck-plan artwork.

## Reference constraints

Official StarTrek.com material describes the Akira class as:

- 464.43 m long
- crew complement 500
- top speed warp 9.8
- a forward three-door launch bay
- an aft landing bay
- a fly-through hangar arrangement through the saucer
- a dorsal weapons pod

A DS9 Technical Manual-derived reference gives the class as 19 decks. TrekMUD treats **19 decks as TECHNICAL_REFERENCE**, not as a directly on-screen-established fact.

## TrekMUD setting fill

The exact internal distribution of rooms and departments is not established on screen. The Meridian therefore uses original `SETTING_FILL` for deck assignments while preserving Akira-class physical constraints.

The topology is intentionally functional rather than hyper-detailed. A deck has stable hubs and important rooms. New rooms can be materialized later without moving already-established rooms.

## Opening continuity retained

The pre-campaign opening proposal established:

- Transporter Room 2 as the arrival point
- quarters on Deck 7, Section 12
- cabin 0712-C

The candidate topology preserves those details:

- `MER-D09-TR-02`
- `MER-D07-COR-12`
- `MER-D07-S12-0712C`

They remain candidates until the ship baseline is approved.

## Geography rules

- stable location IDs are never repurposed;
- approved rooms do not move because a later scene needs convenience;
- story damage changes state, not base geography;
- turbolift, corridor, Jefferies-tube and restricted-access links are explicit edges;
- hidden/secure spaces may exist in GM state without becoming player-visible map knowledge;
- rendered deck diagrams must be generated from or reconciled to the graph.

## Major deck functions

1. Bridge / command
2. Command support / senior officers
3. Officer and diplomatic spaces
4. Science
5. Medical and counseling
6. Recreation / mess / holodecks
7. Junior officers / player quarters
8. Security / training
9. Transporters / operations / computer core
10. Forward flight operations
11. Main fly-through flight deck
12. Shuttle maintenance / cargo
13. Damage control / fabrication
14. Engineering upper
15. Main engineering
16. Engineering lower / auxiliary control
17. Deflector / tactical support
18. Environmental / structural support
19. Antimatter / emergency power / lower sensors

The weapons pod is modeled as separate restricted levels `P1–P3` rather than silently adding numbered decks to the 19-deck hull.
