# Deterministic random system — v1.0

Status: **APPROVED BASELINE — 2026-10-06**.

The purpose of TrekMUD's RNG is not to expose future outcomes. It is to make consequential random results reproducible and auditable after the fact.

## Algorithm

Identifier: `SHA256_COUNTER_V1`

Campaign initialization creates a secret 32-byte seed.

The public campaign state stores:

- algorithm identifier
- SHA-256 commitment of the secret seed
- current counter

The secret seed must be stored only in private GM state. Because TrekMUD is currently public, the live campaign RNG remains **UNINITIALIZED**.

## Draw procedure

For an N-sided die:

1. encode the counter as unsigned 8-byte big-endian;
2. compute SHA-256 over:
   `b"TrekMUD|SHA256_COUNTER_V1|" + seed_bytes + counter_bytes`
3. interpret the 32-byte digest as an unsigned big-endian integer;
4. increment the counter;
5. use rejection sampling to remove modulo bias;
6. return `(integer mod N) + 1`.

If a digest is rejected, the next counter value is consumed and hashed.

A 2d6 check consumes two successful d6 draws.

## Audit record

A consequential roll can record:

- roll ID
- purpose
- counter before
- dice requested
- raw die results
- modifiers
- total
- target
- interpreted outcome
- counter after

The seed itself remains secret during normal play so future rolls cannot be predicted.

If an audit is requested, individual past results can be verified against the seed in private state. Full seed revelation would expose all future rolls and therefore should normally occur only after rotating to a new committed seed.

## Fixed test vector

For a seed of 32 zero bytes and counter 0, the first six d6 draws are:

`3, 5, 4, 1, 6, 4`

This vector exists solely to prove compatible implementations of the algorithm.
