# TrekMUD Lore Source Registry

This registry defines what TrekMUD may ingest, what it may reference, and what it must not redistribute.

| Source | Role | Ingest policy | Notes |
|---|---|---|---|
| STAPI | Primary structured Star Trek entity graph | **Bulk structured ingest** excluding trading-card families | Preserve attribution/provenance and upstream licensing notes |
| Wikidata | Identifier/cross-link enrichment | **Structured ingest** | CC0; use as enrichment, not as authority over stronger canon evidence |
| Memory Alpha | Canon research and chronology | **Reference + attributed factual extraction** | Do not blindly mirror article prose |
| StarTrek.com | Official verification | **Reference links + original summaries** | Do not bulk-copy editorial prose or imagery |
| On-screen episodes/films | Highest canon authority | **Facts and citations only** | Do not store scripts, subtitles, video or audio |
| Fan technical/deck-plan sites | Research/reference | **Reference only by default** | Do not redistribute scans/artwork without a clear compatible license |
| Transcript/script datasets | Dialogue research | **Do not bulk ingest** | A dataset repository cannot place underlying Star Trek scripts into the public domain |

## Source conflict rule

A lower-priority source never silently overwrites a higher-priority fact.

Conflicts are represented explicitly with:

- entity/fact identifier
- competing values
- source references
- confidence
- in-universe effective date if known
- resolution, or `UNRESOLVED`

## Runtime rule

Having a fact in the lore repository does not mean the player character knows it.

Runtime use must distinguish:

1. **canon truth** — what is true in franchise canon;
2. **world truth at the current campaign date** — what is already true by that point;
3. **Starfleet/Federation knowledge** — what the institution could plausibly know;
4. **player-character knowledge** — what this specific character actually knows.

The campaign knowledge file, not the existence of a lore record, determines what can be presented as character knowledge.
