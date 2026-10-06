# TrekMUD Lore Source Registry

This registry defines what TrekMUD may ingest, what it may reference, and what it must not redistribute.

| Source | Role | Ingest policy | Notes |
|---|---|---|---|
| STAPI | Primary structured Star Trek entity graph | **Bulk structured ingest** excluding trading-card families | Mixed upstream licensing; preserve attribution/provenance |
| Wikidata | Identifier/cross-link enrichment | **Structured ingest** | CC0; use small batched/entity queries rather than giant WDQS scans |
| Memory Alpha | Canon research and chronology | **Reference + attributed factual extraction** | CC BY-NC; do not blindly mirror article prose |
| StarTrek.com | Official verification | **Reference links + original summaries** | Do not bulk-copy editorial prose or imagery |
| On-screen episodes/films | Highest canon authority | **Facts and citations only** | Do not store scripts/subtitles/video/audio |
| Fan technical/deck-plan sites | Research/reference | **Reference only by default** | Do not redistribute scans/artwork without a clear compatible license |
| Transcript/script datasets | Dialogue research | **Do not bulk ingest** | A repository claiming its dataset is public domain does not make underlying Star Trek scripts public domain |

## Source conflict rule

A lower-priority source never silently overwrites a higher-priority fact.

Conflicts should be represented explicitly with:

- entity/fact identifier
- competing values
- source references
- confidence
- in-universe effective date if known
- resolution, or `UNRESOLVED`

## Runtime rule

Having a fact in the lore repository does not mean the player character knows it. Runtime access must pass both chronology and character-knowledge gates.
