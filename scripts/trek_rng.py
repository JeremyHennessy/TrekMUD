#!/usr/bin/env python3
"""Deterministic TrekMUD RNG implementation for SHA256_COUNTER_V1."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass

DOMAIN = b"TrekMUD|SHA256_COUNTER_V1|"
ALGORITHM = "SHA256_COUNTER_V1"


@dataclass(frozen=True)
class Draw:
    value: int
    counter_before: int
    counter_after: int
    digest_hex: str


def seed_bytes(seed_hex: str) -> bytes:
    try:
        value = bytes.fromhex(seed_hex)
    except ValueError as exc:
        raise ValueError("seed must be hexadecimal") from exc
    if len(value) != 32:
        raise ValueError("seed must be exactly 32 bytes")
    return value


def commitment(seed_hex: str) -> str:
    return hashlib.sha256(seed_bytes(seed_hex)).hexdigest()


def draw_die(seed_hex: str, counter: int, sides: int) -> Draw:
    if counter < 0:
        raise ValueError("counter must be non-negative")
    if sides < 2:
        raise ValueError("die must have at least 2 sides")

    seed = seed_bytes(seed_hex)
    maximum = 1 << 256
    limit = (maximum // sides) * sides
    current = counter

    while True:
        before = current
        digest = hashlib.sha256(
            DOMAIN + seed + current.to_bytes(8, "big")
        ).digest()
        current += 1
        number = int.from_bytes(digest, "big")
        if number < limit:
            return Draw(
                value=(number % sides) + 1,
                counter_before=before,
                counter_after=current,
                digest_hex=digest.hex(),
            )


def roll(seed_hex: str, counter: int, dice: int, sides: int) -> tuple[list[Draw], int]:
    if dice < 1:
        raise ValueError("dice must be positive")
    draws: list[Draw] = []
    current = counter
    for _ in range(dice):
        item = draw_die(seed_hex, current, sides)
        draws.append(item)
        current = item.counter_after
    return draws, current


def self_test() -> dict[str, object]:
    seed = "00" * 32
    expected = [3, 5, 4, 1, 6, 4]
    draws, counter = roll(seed, 0, len(expected), 6)
    actual = [d.value for d in draws]
    expected_commitment = "66687aadf862bd776c8fc18b8e9f8e20089714856ee233b3902a591d0d5f2925"

    assert actual == expected, (actual, expected)
    assert counter == 6, counter
    assert commitment(seed) == expected_commitment

    # Same seed/counter must reproduce the same sequence exactly.
    repeated, repeated_counter = roll(seed, 0, len(expected), 6)
    assert [d.value for d in repeated] == actual
    assert repeated_counter == counter

    return {
        "algorithm": ALGORITHM,
        "testVector": expected,
        "finalCounter": counter,
        "seedCommitment": expected_commitment,
        "valid": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--seed")
    parser.add_argument("--counter", type=int, default=0)
    parser.add_argument("--dice", type=int, default=2)
    parser.add_argument("--sides", type=int, default=6)
    args = parser.parse_args()

    if args.self_test:
        print(json.dumps(self_test(), indent=2))
        return 0

    if not args.seed:
        parser.error("--seed is required unless --self-test is used")

    draws, final_counter = roll(args.seed, args.counter, args.dice, args.sides)
    print(json.dumps({
        "algorithm": ALGORITHM,
        "commitment": commitment(args.seed),
        "counterBefore": args.counter,
        "counterAfter": final_counter,
        "dice": [d.value for d in draws],
        "total": sum(d.value for d in draws),
        "digests": [d.digest_hex for d in draws],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
