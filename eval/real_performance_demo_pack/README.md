# Real Performance Pack v1

This directory contains the Phase 7 collection contract. It currently contains
no approved audio or annotations, so real-performance metrics are blocked.

Start with [COLLECTION_PROTOCOL.md](COLLECTION_PROTOCOL.md). Evaluation now
requires two distinct annotators per case, pseudonymous performer/session/device
IDs, performer/session/audio separation across splits, annotation bounds, a
frozen collection, and a recomputed held-out audio/label digest. This strengthens
the previously format-only freeze check; it does not populate the pack.

Only owned recordings or sources with a clearly documented compatible license
may enter the pack. Do not infer or fabricate annotations. Every case must
satisfy `manifest.schema.json` and record:

- audio path, SHA-256, duration, and explicit rights basis/reference;
- instrument and chord-isolation or progression category;
- development or held-out split assigned before detector review;
- qualities, playing styles, conditions, and harmonic examples;
- one or more pseudonymous annotators;
- `HIGH`, `MEDIUM`, or `LOW` annotation confidence;
- sorted, non-overlapping timed chord segments.

Do not put names, emails, consent documents, or other personal data in the
manifest. `rights_reference` must point to an approved access-controlled record
or a public license. Audio may remain local when redistribution is not allowed.
User-session audio and feedback never enter this pack automatically.

Collection order: approve provenance, hash audio, assign split, annotate,
freeze held-out labels, run unchanged detectors, capture evidence/runtime, then
perform explicit L1/L2 attribution. Runtime fixtures are not automatically
licensed pack cases.
