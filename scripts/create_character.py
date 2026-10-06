#!/usr/bin/env python3
"""Create TrekMUD's organic revision-1 opening snapshot.

Rules v1.1 requires only identity + department up front. Mechanical traits that
are not yet known remain explicitly unresolved and are discovered through play.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validate_campaign import validate

DEFAULT_ROOT = Path(__file__).resolve().parents[1]

ATTRIBUTES = ("Intellect", "Perception", "Presence", "Resolve", "Physical")
SKILLS = (
    "Command",
    "Conn / Flight Control",
    "Engineering",
    "Operations",
    "Computers",
    "Science",
    "Medicine",
    "Counseling",
    "Security",
    "Tactical",
    "Investigation",
    "Diplomacy / Protocol",
    "Survival / Fieldcraft",
)
DEPARTMENTS = {
    "Engineering": ("ENGINEERING", "Engineering", "Junior Engineering Officer"),
    "Operations": ("OPERATIONS", "Operations", "Junior Operations Officer"),
    "Science": ("SCIENCE", "Science", "Junior Science Officer"),
    "Tactical": ("TACTICAL", "Tactical", "Junior Tactical Officer"),
    "Security": ("SECURITY", "Security", "Junior Security Officer"),
    "Flight Control": ("FLIGHT", "Conn / Flight Control", "Junior Flight Control Officer"),
    "Medical": ("MEDICAL", "Medicine", "Junior Medical Officer"),
    "Counseling": ("COUNSELING", "Counseling", "Junior Counselor"),
}
DEPARTMENT_QUALIFICATIONS = {
    "Engineering": "Starship Engineering Systems Qualification",
    "Operations": "Starship Operations Console Qualification",
    "Science": "Science Sensor and Laboratory Qualification",
    "Tactical": "Starship Tactical Systems Qualification",
    "Security": "Starfleet Security and Phaser Qualification",
    "Flight Control": "Starfleet Shuttlecraft Pilot Qualification",
    "Medical": "Starfleet Medical Officer Certification",
    "Counseling": "Starfleet Counselor Certification",
}


class CharacterCreationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CharacterCreationError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path} must contain a JSON object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def nonempty(value: Any, field: str) -> str:
    require(isinstance(value, str) and value.strip(), f"{field} is required")
    return value.strip()


def validate_selection(selection: dict[str, Any]) -> dict[str, Any]:
    name = nonempty(selection.get("name"), "name")
    species = nonempty(selection.get("species"), "species")
    homeworld = nonempty(selection.get("homeworld"), "homeworld")
    primary_department = nonempty(selection.get("primaryDepartment"), "primaryDepartment")

    require(primary_department in DEPARTMENTS, f"unsupported starting department: {primary_department}")
    department_id, primary_skill, billet = DEPARTMENTS[primary_department]

    age = selection.get("age")
    require(isinstance(age, int) and age > 0, "age must be a positive integer")

    pronouns = selection.get("pronouns")
    require(
        pronouns is None or (isinstance(pronouns, str) and pronouns.strip()),
        "pronouns must be null or non-empty text",
    )

    allowed = {
        "schemaVersion",
        "characterCreationVersion",
        "name",
        "species",
        "age",
        "pronouns",
        "homeworld",
        "primaryDepartment",
    }
    unexpected = sorted(set(selection) - allowed)
    require(
        not unexpected,
        "organic character creation accepts only identity + department; "
        f"move later details into play instead of pre-locking them: {unexpected}",
    )

    return {
        "name": name,
        "species": species,
        "age": age,
        "pronouns": pronouns.strip() if isinstance(pronouns, str) else None,
        "homeworld": homeworld,
        "primaryDepartment": primary_department,
        "departmentId": department_id,
        "primarySkill": primary_skill,
        "billet": billet,
    }


def increment_revision(doc: dict[str, Any], revision: int) -> None:
    require("revision" in doc, "revisioned component missing revision")
    doc["revision"] = revision


def apply_character(root: Path, selection: dict[str, Any]) -> dict[str, Any]:
    normalized = validate_selection(selection)

    state_path = root / "campaign" / "state.json"
    state = load_json(state_path)
    require(state.get("revision") == 0, "character creation requires campaign revision 0")
    require(state.get("status") == "NOT_STARTED", "character creation requires NOT_STARTED campaign")
    require(state.get("rulesVersion") == "1.0", "r00000 must remain the Rules v1.0 historical checkpoint")
    require(
        (state.get("checkpoint") or {}).get("lastCheckpointId") == "r00000",
        "organic character creation requires validated r00000 as its parent",
    )

    components = state["components"]
    docs = {key: load_json(root / rel) for key, rel in components.items()}
    require(docs["character"].get("status") == "UNCREATED", "character already exists")
    require(docs["character"].get("character") is None, "character payload already exists")

    location_ids = {row["id"] for row in docs["locations"].get("locations", [])}
    crew_ids = {row["id"] for row in docs["crew"].get("materializedCrew", [])}
    require("MER-D09-TR-02" in location_ids, "approved opening transporter room missing")
    require("MER-D07-S12-0712C" in location_ids, "approved quarters missing")
    require({"CREW-001", "CREW-002", "CREW-003"}.issubset(crew_ids), "approved command staff missing")

    revision = 1
    character_id = "PC-001"

    for doc in docs.values():
        increment_revision(doc, revision)

    attributes = {name: None for name in ATTRIBUTES}
    skills: dict[str, int | None] = {name: None for name in SKILLS}
    skills[normalized["primarySkill"]] = 2

    character = {
        "id": character_id,
        "creationMode": "ORGANIC_DISCOVERY_V1_1",
        "name": normalized["name"],
        "species": normalized["species"],
        "age": normalized["age"],
        "pronouns": normalized["pronouns"],
        "homeworld": normalized["homeworld"],
        "rank": "Ensign",
        "department": normalized["primaryDepartment"],
        "departmentId": normalized["departmentId"],
        "billet": normalized["billet"],
        "primaryShift": None,
        "attributes": attributes,
        "skills": skills,
        "primarySpecialty": None,
        "secondarySpecialty": None,
        "discoveryState": {
            "attributePoolRemaining": [2, 2, 1, 1, 1],
            "academyRank1SlotsRemaining": 3,
            "departmentSpecialtyAvailable": True,
            "secondarySpecialtyAvailable": True,
            "backgroundFacts": [],
            "personalInterests": [],
            "developmentAreas": [],
            "traits": [],
            "locks": [],
        },
        "health": {
            "injuryState": "Healthy",
            "conditions": [],
            "fatigue": 0,
        },
        "quartersId": "MER-D07-S12-0712C",
        "assignment": {
            "shipId": "USS-MERIDIAN",
            "shipName": "USS Meridian",
            "registry": "NCC-63542",
            "startYear": 2372,
            "startStardate": 49317.4,
        },
    }
    docs["character"]["status"] = "CREATED_DISCOVERING"
    docs["character"]["character"] = character

    docs["serviceRecord"]["characterId"] = character_id
    docs["serviceRecord"]["events"] = [{
        "id": "SR-00001",
        "type": "ASSIGNMENT",
        "year": 2372,
        "stardate": 49317.4,
        "rank": "Ensign",
        "shipId": "USS-MERIDIAN",
        "department": normalized["primaryDepartment"],
        "billet": normalized["billet"],
        "summary": "Reported aboard USS Meridian for initial assignment.",
    }]

    docs["qualifications"]["characterId"] = character_id
    qualification_names = [
        "Starfleet Academy Graduate",
        "Basic EVA Qualification",
        "Starship Emergency Procedures",
        DEPARTMENT_QUALIFICATIONS[normalized["primaryDepartment"]],
    ]
    docs["qualifications"]["records"] = [
        {
            "id": f"QUAL-{i:05d}",
            "name": qual,
            "status": "ACTIVE",
            "source": "STARTING_ASSIGNMENT",
        }
        for i, qual in enumerate(qualification_names, start=1)
    ]

    docs["inventory"]["characterId"] = character_id
    starting_items = [
        ("ITEM-00001", "Starfleet duty uniform", "PERSONAL_ISSUE"),
        ("ITEM-00002", "Starfleet combadge", "PERSONAL_ISSUE"),
        ("ITEM-00003", "Personal PADD", "PERSONAL_ISSUE"),
        ("ITEM-00004", "Starfleet duffel and personal effects", "PERSONAL"),
    ]
    docs["inventory"]["items"] = [
        {"id": item_id, "name": name, "category": category, "status": "IN_POSSESSION"}
        for item_id, name, category in starting_items
    ]

    docs["relationships"]["characterId"] = character_id
    docs["relationships"]["relationships"] = []

    docs["knowledge"]["characterId"] = character_id
    docs["knowledge"]["facts"] = [
        {
            "id": "KN-00001",
            "subject": "USS Meridian",
            "fact": "Assigned vessel is USS Meridian, NCC-63542, Akira-class.",
            "source": "STARFLEET_ASSIGNMENT",
        },
        {
            "id": "KN-00002",
            "subject": "Quarters",
            "fact": "Assigned quarters are Deck 7, Section 12, cabin 0712-C.",
            "source": "PERSONNEL_TRANSFER",
        },
        {
            "id": "KN-00003",
            "subject": "Orientation",
            "fact": "Ship orientation is scheduled for 1400 hours.",
            "source": "PERSONNEL_TRANSFER",
        },
        {
            "id": "KN-00004",
            "subject": "Department",
            "fact": "Report to department head at 1530 hours.",
            "source": "PERSONNEL_TRANSFER",
        },
    ]

    docs["activeThreads"]["threads"] = [{
        "id": "TH-00001",
        "title": "Report aboard USS Meridian",
        "type": "ONBOARDING",
        "status": "ACTIVE",
        "summary": "Complete orientation, settle into quarters and report to the department head.",
    }]

    docs["calendar"]["events"] = [
        {
            "id": "CAL-00001",
            "year": 2372,
            "stardate": 49317.4,
            "shipTime": "14:00",
            "title": "Ship orientation",
            "status": "SCHEDULED",
        },
        {
            "id": "CAL-00002",
            "year": 2372,
            "stardate": 49317.4,
            "shipTime": "15:30",
            "title": "Report to department head",
            "status": "SCHEDULED",
        },
    ]

    # Live RNG initialization still waits for private GM storage.
    docs["rng"]["status"] = "UNINITIALIZED"
    docs["rng"]["counter"] = 0
    docs["rng"]["publicCommitment"] = None

    previous_checkpoint_id = (state.get("checkpoint") or {}).get("lastCheckpointId")
    state["revision"] = revision
    state["rulesVersion"] = "1.1"
    state["status"] = "READY_TO_START"
    state["checkpoint"] = {
        "lastCheckpointId": previous_checkpoint_id,
        "validated": False,
    }
    state["player"] = {
        "characterId": character_id,
        "locationId": "MER-D09-TR-02",
    }
    state["activeThreadIds"] = ["TH-00001"]

    config_path = root / "campaign" / "config.json"
    config = load_json(config_path)
    config["status"] = "ready_to_start"
    config["rulesVersion"] = "1.1"
    config["characterCreationVersion"] = "1.1-organic"

    chronicle_path = root / "campaign" / "CHRONICLE.md"
    chronicle = chronicle_path.read_text(encoding="utf-8").rstrip()
    chronicle += (
        "\n\n## Character creation — revision 1\n\n"
        f"- {normalized['name']} established as a {normalized['species']} Starfleet Ensign.\n"
        f"- Homeworld/upbringing: {normalized['homeworld']}.\n"
        f"- Department: {normalized['primaryDepartment']}.\n"
        f"- Billet: {normalized['billet']}.\n"
        "- Rules upgraded from historical r00000 v1.0 to Rules v1.1 Organic Character Discovery.\n"
        "- Attributes, Academy cross-training, specialties, interests and detailed background remain intentionally unresolved.\n"
        "- Opening position remains Transporter Room 2 at 1217 hours; no narrative action has occurred.\n"
    )

    for key, rel in components.items():
        write_json(root / rel, docs[key])
    write_json(state_path, state)
    write_json(config_path, config)
    chronicle_path.write_text(chronicle + "\n", encoding="utf-8")

    result = validate(root)
    require(result["valid"] is True and result["revision"] == 1, "post-creation campaign validation failed")
    return {
        "valid": True,
        "revision": 1,
        "rulesVersion": "1.1",
        "status": state["status"],
        "characterId": character_id,
        "name": normalized["name"],
        "department": normalized["primaryDepartment"],
        "billet": normalized["billet"],
        "unresolvedAttributes": 5,
        "academyRank1SlotsRemaining": 3,
        "specialtySlotsRemaining": 2,
        "locationId": "MER-D09-TR-02",
        "quartersId": "MER-D07-S12-0712C",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    selection = load_json(args.input.resolve())
    normalized = validate_selection(selection)
    if args.validate_only:
        print(json.dumps({"valid": True, "selection": normalized}, indent=2))
        return 0

    result = apply_character(args.root.resolve(), selection)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
