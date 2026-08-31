# HorizonJam Publication Workspace

This directory turns the frozen HorizonJam v3 research baseline into a
publication-first open-source narrative. These documents are drafts, not
evidence that the prototype is production ready or that its research
hypotheses have been confirmed.

## Reading Order

1. [ABSTRACT.md](ABSTRACT.md): submission-length abstract and claim boundary.
2. [PAPER_DRAFT.md](PAPER_DRAFT.md): venue-neutral systems-paper draft.
3. [OPEN_SOURCE_POST.md](OPEN_SOURCE_POST.md): public architecture article.
4. [COMPETITIVE_LANDSCAPE.md](COMPETITIVE_LANDSCAPE.md): sourced product and
   research comparison.
5. [PUBLICATION_TO_PRODUCTION.md](PUBLICATION_TO_PRODUCTION.md): gated sequence
   from v3 publication through private alpha, web release, and mobile stores.

## Canonical Evidence

Publication claims must resolve to one of these sources:

- [STATUS.md](../../STATUS.md) for current verified state;
- [V3_BASELINE.md](../releases/V3_BASELINE.md) for the frozen source baseline;
- [EVALUATION.md](../context/EVALUATION.md) for methods and limitations;
- checked-in reports under `eval/` for measurements;
- source and tests for implemented behavior; and
- [research/detector_tournament](../../research/detector_tournament/README.md)
  for proposed, not completed, multi-source experiments.

## Publication Rules

- Call HorizonJam a research prototype until the public-release gates pass.
- Call synthetic evidence synthetic and post-transcription evidence
  post-transcription.
- Do not claim state-of-the-art chord recognition or improved learning
  outcomes.
- Do not claim competitors lack an internal capability. Compare only public
  product descriptions and published architecture.
- Treat multi-source fusion, confidence calibration, and learner outcomes as
  hypotheses until measured.
- Date volatile market observations and prefer official product listings.
- Resolve dataset, model-weight, corpus, and repository licensing before an
  open-source release announcement.

## Publication Metadata Still Needed

- author publication name, affiliation, and ORCID;
- target venue and page/template constraints;
- repository license and third-party notice policy;
- archived release DOI, such as a Zenodo record;
- approved real-audio dataset and participant protocol; and
- final artifact hashes and reproducibility environment.
