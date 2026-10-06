#!/usr/bin/env python3
"""Validate the candidate USS Meridian crew structure and directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path} must contain an object")
    return value


def validate(structure_path: Path, directory_path: Path) -> dict[str, Any]:
    structure = load(structure_path)
    directory = load(directory_path)

    require(structure.get("schemaVersion") == 1, "crew structure schemaVersion must be 1")
    require(directory.get("schemaVersion") == 1, "crew directory schemaVersion must be 1")
    require(structure.get("shipId") == "USS-MERIDIAN", "crew structure shipId mismatch")
    require(directory.get("shipId") == "USS-MERIDIAN", "crew directory shipId mismatch")

    nominal = structure.get("nominalComplement")
    require(nominal == 500, "Meridian nominal complement must be 500")

    departments = structure.get("departments")
    require(isinstance(departments, list) and departments, "departments must be non-empty")
    department_ids: set[str] = set()
    department_total = 0
    for index, row in enumerate(departments):
        require(isinstance(row, dict), f"departments[{index}] must be an object")
        dep_id = row.get("id")
        require(isinstance(dep_id, str) and dep_id, f"departments[{index}].id required")
        require(dep_id not in department_ids, f"duplicate department id: {dep_id}")
        department_ids.add(dep_id)
        count = row.get("nominalPersonnel")
        require(isinstance(count, int) and count > 0, f"{dep_id} personnel must be positive")
        department_total += count
    require(department_total == nominal, f"department total {department_total} != complement {nominal}")

    shift_model = structure.get("shiftModel")
    require(isinstance(shift_model, dict), "shiftModel required")
    shifts = shift_model.get("shifts")
    require(isinstance(shifts, list) and shifts, "shiftModel.shifts must be non-empty")
    shift_ids: set[str] = set()
    shift_total = 0
    for index, row in enumerate(shifts):
        require(isinstance(row, dict), f"shifts[{index}] must be an object")
        shift_id = row.get("id")
        require(isinstance(shift_id, str) and shift_id, f"shifts[{index}].id required")
        require(shift_id not in shift_ids, f"duplicate shift id: {shift_id}")
        shift_ids.add(shift_id)
        count = row.get("nominalPersonnel")
        require(isinstance(count, int) and count > 0, f"{shift_id} personnel must be positive")
        shift_total += count
    require(shift_total == nominal, f"shift total {shift_total} != complement {nominal}")
    require(shift_ids == {"ALPHA", "BETA", "GAMMA"}, "candidate baseline must use Alpha/Beta/Gamma shifts")

    people = directory.get("people")
    require(isinstance(people, list) and people, "directory people must be non-empty")
    require(len(people) < nominal, "candidate should not materialize the entire crew")

    ids: set[str] = set()
    names: set[str] = set()
    for index, person in enumerate(people):
        require(isinstance(person, dict), f"people[{index}] must be an object")
        person_id = person.get("id")
        name = person.get("name")
        require(isinstance(person_id, str) and person_id.startswith("CREW-"), f"invalid crew id at index {index}")
        require(person_id not in ids, f"duplicate crew id: {person_id}")
        ids.add(person_id)
        require(isinstance(name, str) and name, f"{person_id} name required")
        require(name not in names, f"duplicate crew name: {name}")
        names.add(name)
        require(person.get("tier") in {1, 2}, f"{person_id} must be tier 1 or 2")
        require(person.get("department") in department_ids, f"{person_id} has unknown department")
        require(person.get("primaryShift") in shift_ids, f"{person_id} has unknown shift")
        require(person.get("status") == "ACTIVE", f"{person_id} must begin ACTIVE")
        require(isinstance(person.get("rank"), str) and person["rank"], f"{person_id} rank required")
        require(isinstance(person.get("billet"), str) and person["billet"], f"{person_id} billet required")

    # Command chain and department leadership.
    billets = {person["billet"]: person for person in people}
    require("Commanding Officer" in billets, "missing commanding officer")
    require("Executive Officer" in billets, "missing executive officer")

    required_leadership = {
        "ENGINEERING": "Chief Engineer",
        "OPERATIONS": "Chief Operations Officer / Second Officer",
        "SCIENCE": "Chief Science Officer",
        "MEDICAL": "Chief Medical Officer",
        "SECURITY": "Chief Security Officer",
        "TACTICAL": "Chief Tactical Officer",
        "FLIGHT": "Chief Flight Control Officer",
        "COUNSELING": "Chief Counselor",
        "LOGISTICS": "Chief Logistics Officer",
    }
    for department, billet in required_leadership.items():
        require(billet in billets, f"missing required billet: {billet}")
        require(billets[billet]["department"] == department, f"{billet} department mismatch")

    # Opening continuity.
    transporter = next((p for p in people if p.get("openingContinuity") and p["billet"] == "Transporter Chief"), None)
    require(transporter is not None, "opening transporter chief must be materialized")
    require(transporter.get("name") == "Lian Okafor", "opening transporter chief identity drift")

    bolian = next((p for p in people if p.get("openingContinuity") and p.get("species") == "Bolian"), None)
    require(bolian is not None, "opening Bolian crewman must be materialized")
    require(bolian.get("rank") == "Crewman", "opening Bolian must remain a crewman")

    # Candidate neighboring quarters must remain distinct.
    quarters = [p.get("quartersCandidate") for p in people if p.get("quartersCandidate")]
    require(len(quarters) == len(set(quarters)), "duplicate candidate quarters assignments")
    for value in quarters:
        require(isinstance(value, str) and value.startswith("MER-D07-S12-0712"), f"invalid candidate quarters id: {value}")

    return {
        "valid": True,
        "nominalComplement": nominal,
        "departmentTotal": department_total,
        "shiftTotal": shift_total,
        "materializedCrew": len(people),
        "tier1": sum(1 for p in people if p["tier"] == 1),
        "tier2": sum(1 for p in people if p["tier"] == 2),
        "departments": len(department_ids),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--structure",
        type=Path,
        default=ROOT / "world" / "meridian" / "crew-structure.json",
    )
    parser.add_argument(
        "--directory",
        type=Path,
        default=ROOT / "world" / "meridian" / "crew-directory.json",
    )
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.structure.resolve(), args.directory.resolve()), indent=2))
        return 0
    except (ValidationError, OSError, json.JSONDecodeError) as exc:
        print(f"INVALID MERIDIAN CREW MODEL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
