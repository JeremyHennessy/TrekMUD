# TrekMUD character creation

Character creation happens only after Rules v1.0 and the pre-character world baseline are valid.

The player begins as a newly assigned **Starfleet Ensign** aboard USS Meridian.

## Player choices

The player chooses:

1. **Name**
2. **Species**
3. **Age**
4. **Pronouns** (optional)
5. **Homeworld / place of upbringing**
6. **Primary department**
7. **Primary specialty**
8. **Secondary specialty**
9. **Attribute assignment** using exactly `2, 2, 1, 1, 1`
10. **Secondary/supporting broad skill**
11. **Two Academy cross-training skills**
12. **One personal interest**
13. **One development area** — a real weakness, blind spot or area the officer wants to improve
14. **Short background**

Personality is not locked into an alignment or archetype. It can emerge through play.

## Starting departments

Normal starting Ensign departments:

- Engineering
- Operations
- Science
- Tactical
- Security
- Flight Control
- Medical
- Counseling

A different Starfleet path can be proposed if it makes sense in 2372.

## Species

Any canon species plausibly serving in Starfleet in 2372 can be proposed.

Common straightforward options include Human, Vulcan, Andorian, Tellarite, Betazoid, Trill, Bolian and Benzite. Bajoran or less common Federation/non-Federation backgrounds can work with a plausible Starfleet Academy history.

Species never forces a personality stereotype. Biological/cultural traits are explicit character traits, not assumptions about every individual.

## Locked mechanical baseline

Per Rules v1.0:

- attributes are exactly `2, 2, 1, 1, 1`;
- primary department skill begins at rank 2;
- one secondary/supporting broad skill begins at rank 1;
- two distinct Academy cross-training skills begin at rank 1;
- all other broad skills begin at rank 0 unless an explicitly approved trait says otherwise;
- primary and secondary specialties each grant +1 when directly relevant, but only one specialty applies to a single check.

## What the setup tool creates

After choices are confirmed, `scripts/create_character.py` creates revision 1:

- player character record;
- Ensign service/assignment record;
- starting qualifications;
- standard personal issue;
- opening knowledge;
- onboarding calendar items;
- onboarding thread;
- player location at Transporter Room 2;
- quarters assignment to Deck 7, Section 12, 0712-C.

The story still has not advanced. Revision 1 represents the exact instant immediately after materializing aboard USS Meridian at 1217 hours.

A validated `r00001` checkpoint is created before the first narrative action.
