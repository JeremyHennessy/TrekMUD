# Lore sources and provenance

TrekMUD stores structured facts, compact summaries written for the game, and source references. It does not mirror episode scripts, subtitles, copyrighted reference books, or full encyclopedia articles.

## STAPI — primary structured ingestion

- Source: https://stapi.co/
- Purpose: normalized Star Trek entities and relationships: characters, species, episodes, spacecraft, locations, organizations, technology, conflicts, occupations and many other entity classes.
- Access: public REST API; no API key required.
- Upstream statement: STAPI says its data is derived mainly from Memory Alpha, with some Memory Beta and other sources.
- Licensing: STAPI states most derived content should be treated as **CC BY-NC 4.0**, some Memory Beta-derived content as **CC BY-SA 3.0**, and some source-code-originated data as MIT.
- Exclusion: STAPI specifically says trading-card data from StarTrekCards.com should be considered copyrighted. TrekMUD does not ingest the trading-card resource families.
- Attribution: preserve this file and the generated manifest with every redistributed snapshot.

## Wikidata — enrichment source

- Source: https://www.wikidata.org/
- Purpose: CC0 structured identifiers and cross-links where useful.
- Licensing: Wikidata structured data is released under **CC0**.
- Status: enrichment layer follows the STAPI baseline; it must never overwrite a higher-confidence canon fact without a recorded conflict.

## StarTrek.com — canonical reference links

- Source: https://www.startrek.com/
- Purpose: official series/episode/context references and verification.
- Policy: link/cite and summarize factual points; do not scrape or redistribute article prose or imagery.

## Memory Alpha

- Source: https://memory-alpha.fandom.com/
- Purpose: high-value canon research reference and upstream source used by STAPI.
- Licensing: Memory Alpha content is CC BY-NC. TrekMUD may record references and original factual summaries with attribution, but should not bulk-copy article prose.

## Source precedence

When sources conflict:

1. on-screen/film canon
2. official canonical reference material where clearly authoritative
3. structured STAPI/Memory Alpha facts
4. Wikidata or secondary indexes
5. TrekMUD setting fill

Conflicts are recorded rather than silently resolved by guesswork.
