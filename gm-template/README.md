# TrekMUD private GM-state template

This directory contains **schema/example files only**.

It must never contain actual campaign secrets while the repository is public.

The live hidden state should exist in either:

1. a private TrekMUD repository; or
2. a separate private companion repository such as `TrekMUD-GM`.

## Hidden state belongs there

Private GM state may contain:

- unrevealed NPC motives and opinions;
- hidden relationship values;
- mystery solutions;
- antagonist plans;
- off-screen events;
- future event clocks;
- secret mission information;
- the deterministic RNG secret seed.

## Synchronization rule

Every private save must identify:

- the public campaign revision;
- the public checkpoint ID;
- the public repository commit it corresponds to.

If public and private revisions disagree, do not improvise which one is newer. Reconcile them explicitly before resuming play.

## RNG rule

The public repository stores only:

- algorithm identifier;
- SHA-256 seed commitment;
- consumed counter.

The 32-byte secret seed exists only in private GM storage.

The template deliberately contains no usable seed.
