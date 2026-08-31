---
name: rag-change
description: Change HorizonJam retrieval, Chroma schemas, query construction, corpus ingestion, embeddings, provenance, or prompt retrieval packets with relevance and grounding evidence. Use for unified_rag_system.py, RAG ingestion scripts, vector stores, retrieval configuration, or source/citation behavior.
---

# Change Retrieval Safely

1. Read `docs/context/ARCHITECTURE.md#rag-graph`, `docs/context/HARNESS.md#retrieval-context`, `docs/context/EVALUATION.md`, and `docs/context/SECURITY.md`.
2. Identify whether the task affects serving, ingestion, record schema, embedding space, query construction, ranking, or tutor context.
3. Identify the authoritative collection/path and source provenance. If either is unknown, do not ingest or redistribute questionable data.
4. Capture representative current query/results before editing, including IDs, sources, distances, and exact context passed to the tutor.
5. Define fixed relevance/grounding cases and acceptance criteria.
6. Make the smallest layer-appropriate change. Keep ingestion out of request serving unless explicitly justified.
7. Test empty collection, missing key, no results, malformed metadata, duplicate records, and provider failure as relevant.
8. Compare before/after relevance, coverage, provenance, prompt context, latency, and embedding/API cost.
9. Inspect whether retrieved text, not only metadata, reaches the model and whether source provenance survives.

Never claim grounding from successful retrieval alone. Record corpus version, embedding model, collection, query set, rubric, failures, and commands.
