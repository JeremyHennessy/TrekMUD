#!/usr/bin/env python3
"""Build a reproducible Star Trek lore catalogue from STAPI.

The scraper stores reusable structured records, not article prose. It discovers
STAPI resources, resolves working endpoint versions, downloads catalogue pages
with bounded concurrency, and hydrates TNG/DS9 episodes for era-specific play.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://stapi.co/api"
PAGE_SIZE = 100
USER_AGENT = "TrekMUD-lore-ingest/0.2 (+https://github.com/JeremyHennessy/TrekMUD)"
PRINT_LOCK = Lock()

FALLBACK_RESOURCES = {
    "animal", "astronomicalObject", "book", "bookCollection", "bookSeries",
    "character", "comic", "comicCollection", "comicSeries", "comicStrip",
    "comics", "company", "conflict", "element", "episode", "food",
    "literature", "location", "magazine", "magazineSeries", "material",
    "medicalCondition", "movie", "occupation", "organization", "performer",
    "season", "series", "soundtrack", "spacecraft", "spacecraftClass",
    "species", "staff", "technology", "title", "videoGame", "videoRelease",
    "weapon",
}

EXCLUDED_RESOURCES = {"tradingCard", "tradingCardDeck", "tradingCardSet"}

CRITICAL_LORE = {
    "animal", "astronomicalObject", "character", "conflict", "element",
    "episode", "food", "location", "material", "medicalCondition",
    "occupation", "organization", "season", "series", "spacecraft",
    "spacecraftClass", "species", "technology", "title", "weapon",
}

PRIMARY_SERIES = {"TNG", "DS9"}


@dataclass
class FetchResult:
    resource: str
    version: int
    records: list[dict[str, Any]]
    collection_key: str
    pages: int


def log(message: str, *, error: bool = False) -> None:
    with PRINT_LOCK:
        print(message, file=sys.stderr if error else sys.stdout, flush=True)


def http_text(
    url: str,
    params: dict[str, Any] | None = None,
    retries: int = 4,
) -> str:
    if params:
        url = f"{url}?{urlencode(params)}"
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
                },
            )
            with urlopen(req, timeout=45) as response:
                return response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            last = exc
            if isinstance(exc, HTTPError) and exc.code in {400, 401, 403, 404}:
                raise
            time.sleep(min(8, 1.25 * (2**attempt)))
    assert last is not None
    raise last


def http_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return json.loads(http_text(url, params=params))


def discover_resources() -> dict[str, int]:
    versions: dict[str, int] = {}
    try:
        html = http_text(f"{BASE}/")
        for ver, resource in re.findall(
            r"/api/v(\d+)/rest/([A-Za-z][A-Za-z0-9]*)",
            html,
        ):
            versions[resource] = max(int(ver), versions.get(resource, 0))
    except Exception as exc:
        log(f"warning: service discovery failed: {exc}", error=True)

    discovered = {r: v for r, v in versions.items() if r != "common"}
    if not discovered:
        for resource in FALLBACK_RESOURCES | EXCLUDED_RESOURCES:
            discovered[resource] = 3
    return discovered


def collection_key(payload: dict[str, Any]) -> str:
    candidates = [
        k for k, v in payload.items()
        if k not in {"page", "sort"} and isinstance(v, list)
    ]
    if len(candidates) != 1:
        raise ValueError(
            f"could not identify unique collection key; candidates={candidates}"
        )
    return candidates[0]


def version_candidates(preferred: int) -> list[int]:
    # Discovery can expose a newer detail endpoint while /search exists only in
    # an older REST version. Probe downward deterministically.
    values = [v for v in range(max(1, preferred), 0, -1)]
    return values or [1]


def probe_search_version(resource: str, preferred: int) -> int:
    errors: list[str] = []
    for version in version_candidates(preferred):
        endpoint = f"{BASE}/v{version}/rest/{resource}/search"
        try:
            payload = http_json(
                endpoint,
                {"pageNumber": 0, "pageSize": 1},
            )
            if "page" in payload:
                collection_key(payload)
                return version
            errors.append(f"v{version}: no page metadata")
        except HTTPError as exc:
            errors.append(f"v{version}: HTTP {exc.code}")
        except Exception as exc:
            errors.append(f"v{version}: {exc}")
    raise RuntimeError(
        f"no working search endpoint for {resource}; " + "; ".join(errors)
    )


def fetch_catalog(
    resource: str,
    preferred_version: int,
    delay: float,
) -> FetchResult:
    version = probe_search_version(resource, preferred_version)
    if version != preferred_version:
        log(
            f"{resource}: discovery preferred v{preferred_version}; "
            f"using working search v{version}"
        )

    endpoint = f"{BASE}/v{version}/rest/{resource}/search"
    first = http_json(
        endpoint,
        {"pageNumber": 0, "pageSize": PAGE_SIZE},
    )
    key = collection_key(first)
    page = first.get("page") or {}
    total_pages = int(page.get("totalPages") or 1)
    records = list(first[key])

    for page_no in range(1, total_pages):
        if delay:
            time.sleep(delay)
        payload = http_json(
            endpoint,
            {"pageNumber": page_no, "pageSize": PAGE_SIZE},
        )
        if collection_key(payload) != key:
            raise ValueError(
                f"collection key changed for {resource} page {page_no}"
            )
        records.extend(payload[key])

    records.sort(
        key=lambda row: (
            str(row.get("uid", "")),
            str(row.get("name", row.get("title", ""))),
        )
    )
    return FetchResult(resource, version, records, key, total_pages)


def full_record(resource: str, version: int, uid: str) -> dict[str, Any]:
    return http_json(
        f"{BASE}/v{version}/rest/{resource}",
        {"uid": uid},
    )


def record_series_abbreviation(record: dict[str, Any]) -> str | None:
    series = record.get("series")
    if isinstance(series, dict):
        value = series.get("abbreviation")
        return str(value) if value else None
    return None


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def fetch_one_resource(
    resource: str,
    preferred_version: int,
    delay: float,
) -> tuple[str, FetchResult | None, dict[str, Any] | None]:
    log(f"fetching {resource}; preferred v{preferred_version}")
    try:
        result = fetch_catalog(resource, preferred_version, delay)
        log(
            f"completed {resource}: {len(result.records)} records "
            f"via v{result.version} across {result.pages} pages"
        )
        return resource, result, None
    except Exception as exc:
        failure = {
            "resource": resource,
            "preferredVersion": preferred_version,
            "error": str(exc),
            "critical": resource in CRITICAL_LORE,
        }
        log(f"ERROR {resource}: {exc}", error=True)
        return resource, None, failure


def build_era_data(
    tmp_root: Path,
    results: dict[str, FetchResult],
    delay: float,
    workers: int,
) -> dict[str, Any]:
    episode_result = results.get("episode")
    if not episode_result:
        return {"status": "skipped", "reason": "episode catalogue unavailable"}

    era_headers = [
        ep for ep in episode_result.records
        if record_series_abbreviation(ep) in PRIMARY_SERIES
    ]
    candidates = era_headers or episode_result.records

    full_episodes: list[dict[str, Any]] = []
    character_headers: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, str]] = []

    def hydrate(header: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
        uid = header.get("uid")
        if not uid:
            return None, None
        if delay:
            time.sleep(delay)
        try:
            payload = full_record(
                "episode",
                episode_result.version,
                str(uid),
            )
            episode = (
                payload.get("episode")
                if isinstance(payload.get("episode"), dict)
                else payload
            )
            if record_series_abbreviation(episode) not in PRIMARY_SERIES:
                return None, None
            return episode, None
        except Exception as exc:
            return None, f"{uid}: {exc}"

    # Bound detail hydration separately so the API is not flooded.
    hydrate_workers = max(1, min(workers, 4))
    with ThreadPoolExecutor(max_workers=hydrate_workers) as executor:
        futures = [executor.submit(hydrate, header) for header in candidates]
        for future in as_completed(futures):
            episode, error = future.result()
            if error:
                uid, message = error.split(": ", 1)
                failures.append({"uid": uid, "error": message})
                continue
            if episode is None:
                continue
            full_episodes.append(episode)
            for character in episode.get("characters", []) or []:
                if isinstance(character, dict) and character.get("uid"):
                    character_headers[str(character["uid"])] = character

    full_episodes.sort(
        key=lambda row: (
            record_series_abbreviation(row) or "",
            int(row.get("seasonNumber") or 0),
            int(row.get("episodeNumber") or 0),
            str(row.get("uid", "")),
        )
    )
    characters = sorted(
        character_headers.values(),
        key=lambda row: (
            str(row.get("name", "")),
            str(row.get("uid", "")),
        ),
    )

    write_json(
        tmp_root / "era" / "tng-ds9-episodes.json",
        {
            "description": "Full STAPI episode records for TNG and DS9",
            "series": sorted(PRIMARY_SERIES),
            "count": len(full_episodes),
            "records": full_episodes,
        },
    )
    write_json(
        tmp_root / "era" / "tng-ds9-characters.json",
        {
            "description": (
                "Character headers related by STAPI to TNG/DS9 episode records"
            ),
            "count": len(characters),
            "records": characters,
        },
    )

    return {
        "status": "ok" if not failures else "partial",
        "episodeCount": len(full_episodes),
        "characterCount": len(characters),
        "hydrateFailures": sorted(
            failures,
            key=lambda row: row["uid"],
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="data/stapi",
        help="Generated STAPI directory",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.05,
        help="Per-resource/page request spacing in seconds",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Concurrent resource workers (1-8)",
    )
    parser.add_argument("--skip-era-hydration", action="store_true")
    args = parser.parse_args()

    workers = max(1, min(args.workers, 8))
    out_root = Path(args.output)
    tmp_root = out_root.with_name(out_root.name + ".tmp")
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    (tmp_root / "catalog").mkdir(parents=True, exist_ok=True)

    fetched_at = datetime.now(timezone.utc).isoformat()
    discovered = discover_resources()
    resources = sorted(
        r for r in discovered
        if r not in EXCLUDED_RESOURCES and r != "common"
    )

    results: dict[str, FetchResult] = {}
    failures: list[dict[str, Any]] = []

    log(
        f"discovered {len(discovered)} resources; fetching "
        f"{len(resources)} reusable resources with {workers} workers"
    )

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                fetch_one_resource,
                resource,
                discovered[resource],
                args.delay,
            ): resource
            for resource in resources
        }
        for future in as_completed(futures):
            resource, result, failure = future.result()
            if result is not None:
                results[resource] = result
                write_json(
                    tmp_root / "catalog" / f"{resource}.json",
                    {
                        "source": "STAPI",
                        "endpoint": (
                            f"{BASE}/v{result.version}/rest/"
                            f"{resource}/search"
                        ),
                        "apiVersion": result.version,
                        "resource": resource,
                        "collectionKey": result.collection_key,
                        "fetchedAt": fetched_at,
                        "count": len(result.records),
                        "records": result.records,
                    },
                )
            if failure is not None:
                failures.append(failure)

    era = {"status": "skipped"}
    if not args.skip_era_hydration:
        log("hydrating TNG/DS9 episode relationships")
        era = build_era_data(
            tmp_root,
            results,
            args.delay,
            workers,
        )

    manifest = {
        "schemaVersion": 2,
        "source": "STAPI",
        "sourceUrl": "https://stapi.co/",
        "fetchedAt": fetched_at,
        "licenseNote": (
            "See lore/SOURCES.md; most STAPI-derived content is treated as "
            "CC BY-NC 4.0, with mixed upstream licensing."
        ),
        "workerCount": workers,
        "discoveredResourceVersions": dict(sorted(discovered.items())),
        "excludedResources": sorted(
            EXCLUDED_RESOURCES & set(discovered)
        ),
        "resourcesFetched": {
            name: {
                "preferredVersion": discovered.get(name),
                "resolvedVersion": result.version,
                "count": len(result.records),
                "pages": result.pages,
            }
            for name, result in sorted(results.items())
        },
        "failures": sorted(
            failures,
            key=lambda row: row["resource"],
        ),
        "era": era,
        "totalRecords": sum(
            len(result.records) for result in results.values()
        ),
    }
    write_json(tmp_root / "manifest.json", manifest)

    critical_failures = [f for f in failures if f["critical"]]
    if critical_failures:
        log(
            f"fatal: {len(critical_failures)} critical lore resources failed; "
            "preserving previous generated dataset",
            error=True,
        )
        shutil.rmtree(tmp_root)
        return 2

    if out_root.exists():
        readme = out_root / "README.md"
        readme_text = (
            readme.read_text(encoding="utf-8")
            if readme.exists()
            else None
        )
        shutil.rmtree(out_root)
        tmp_root.rename(out_root)
        if readme_text is not None:
            (out_root / "README.md").write_text(
                readme_text,
                encoding="utf-8",
            )
    else:
        tmp_root.rename(out_root)

    print(
        json.dumps(
            {
                "totalRecords": manifest["totalRecords"],
                "failures": len(failures),
                "criticalFailures": 0,
                "era": era,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
