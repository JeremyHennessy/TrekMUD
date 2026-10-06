# Canon and chronology policy

## Era

TrekMUD begins in **2372** at stardate **49317.4**. The primary tonal/cultural reference is the overlap of late *The Next Generation* and *Deep Space Nine*.

Primary sources for era modelling:

- Star Trek: The Next Generation
- Star Trek: Deep Space Nine

Supporting canon:

- earlier televised/film canon as established history
- Voyager-era facts only when they are plausibly known in the Alpha/Beta Quadrants at the campaign date
- later canon may constrain future continuity, but is GM-only until the in-universe clock reaches it

## Knowledge gates

The lore database may contain information from years after 2372. That **does not make it character knowledge**.

Every runtime lore lookup should distinguish:

- `canon_fact`: what is true in franchise canon
- `effective_from`: earliest in-universe date/stardate the fact is true
- `known_to_federation_from`: earliest point Starfleet/Federation could plausibly know it
- `known_to_player`: campaign-specific knowledge
- `source`: provenance

When a precise effective date is unavailable, the fact must be marked uncertain instead of guessed.

## Divergence policy

TrekMUD can diverge locally through the USS Meridian and its crew. It must not casually overwrite major established events. If player action could plausibly affect a major canon event, record the divergence explicitly in the campaign chronicle and canon-delta log.

## Canon confidence

Use four levels:

- `CANON_CONFIRMED` — directly supported by televised/film canon or an authoritative canonical reference
- `CANON_DERIVED` — strongly inferred from canonical facts but not explicitly stated
- `SETTING_FILL` — plausible detail invented to make the simulation function without contradicting canon
- `TREKMUD_ORIGINAL` — explicitly original campaign material

Never present `SETTING_FILL` as franchise canon.
