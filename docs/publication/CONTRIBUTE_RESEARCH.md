# Contributing to HorizonJam Research

HorizonJam welcomes research and engineering contributions that make AI music tutoring more measurable, reproducible, and trustworthy.

The project is currently a research prototype. The most useful contributions are not additional features for their own sake; they are improvements that help answer a clear research question or remove a known product limitation.

## Research Goal

HorizonJam studies how uncertain musical observations should be represented before a language model turns them into tutoring feedback.

A contribution is especially valuable when it improves one of these links:

```text
performance
   ↓
audio / note evidence
   ↓
chord and harmonic interpretation
   ↓
retrieved knowledge
   ↓
AI explanation
   ↓
practice guidance
```

## High-Value Contribution Areas

### 1. Real-performance evaluation

We need owned or clearly licensed short performances with reliable annotations.

Useful work includes:

- guitar and piano recordings;
- major, minor, dominant seventh, major seventh, and minor seventh chords;
- inversions and partial voicings;
- strumming and arpeggiation;
- varied microphones and rooms;
- background noise;
- explicit no-chord regions;
- annotation tools and agreement studies.

Do not submit copyrighted commercial recordings without clear permission.

### 2. External chord-recognition baselines

The current research plan includes independent baselines such as LV-Chordia, BTC, CREMA, Chordino/NNLS Chroma, and lightweight chroma methods.

A useful baseline contribution should include:

- source and license;
- model/checkpoint provenance;
- isolated environment;
- exact version/hash;
- normalized output adapter;
- runtime measurements;
- reproducible evaluation command; and
- documented limitations.

Do not silently add a model to the product path.

### 3. Interpretable harmonic analysis

We are interested in methods that provide evidence a researcher can inspect, including:

- constant-Q/chroma features;
- bass-sensitive chroma;
- tuning correction;
- harmonic-change detection;
- chord-template comparison;
- beat-aware segmentation;
- temporal decoding; and
- instrument-aware priors.

### 4. Uncertainty and calibration

Current detector confidence is incomplete and should not be treated as calibrated probability.

Useful research questions include:

- how candidate margins relate to correctness;
- whether detector agreement predicts reliability;
- whether note confidence and chroma evidence improve uncertainty estimates;
- how disagreement should be shown to the tutor or musician; and
- whether uncertainty-aware feedback reduces unsupported claims.

### 5. Retrieval and tutoring evaluation

The tutor currently preserves retrieved text and source provenance.

Useful contributions include labeled evaluation sets for:

- retrieval relevance;
- source coverage;
- unsupported claims;
- uncertainty wording;
- musical correctness;
- actionability; and
- pedagogical appropriateness.

Expert-rater protocols are especially valuable.

### 6. Reproducibility and research infrastructure

Contributions are welcome around:

- dependency locking;
- reproducible research environments;
- dataset acquisition and hash verification;
- experiment manifests;
- machine-readable reports;
- CI for research tests;
- artifact verification; and
- archival release preparation.

### 7. Research interface and accessibility

The browser interface should eventually help users and researchers inspect:

- detected chords;
- timing;
- warnings;
- alternative interpretations when available;
- supporting evidence;
- retrieved sources; and
- feedback rationale.

Accessibility and clear visualization are research-quality concerns, not cosmetic extras.

## Contribution Principles

### Make one claim at a time

Prefer a controlled experiment over a large rewrite.

### Preserve the baseline

New detector work should remain experimental until it beats the frozen baseline under a documented evaluation.

### Separate measurements from interpretation

Report what was measured before explaining why it may have happened.

### Do not inflate confidence

Raw neural scores, rule weights, and candidate margins are not automatically probabilities.

### Keep synthetic and real evidence separate

Synthetic tests are useful for diagnosis and regression. They are not evidence of real-musician performance.

### Record provenance

Every external dataset, model, checkpoint, code dependency, or media fixture should have a documented source and license status.

## Suggested Contribution Format

A research contribution should ideally state:

1. **Question** — what are you trying to learn?
2. **Baseline** — what existing behavior are you comparing against?
3. **Change** — what single variable or method changes?
4. **Dataset** — what evidence is used?
5. **Metrics** — how is success measured?
6. **Result** — what happened?
7. **Failure cases** — where did it get worse or remain weak?
8. **Reproducibility** — how can another person rerun it?
9. **Product implication** — does the result justify any product change?

## Before Opening a Pull Request

Please confirm that:

- the change has a clear research or product motivation;
- existing relevant tests pass;
- new measurements are reproducible;
- generated artifacts are intentional;
- licensing/provenance is documented;
- unsupported claims were not added to README or paper material; and
- production detector behavior was not changed accidentally.

## Collaboration

If you are interested in contributing a detector baseline, dataset, annotation protocol, music-education evaluation, or reproducibility improvement, open a focused issue describing the research question and proposed evidence.

Good first discussions are narrow. For example:

- "Benchmark LV-Chordia on the first real-performance pack"
- "Add an interpretable CQT/chroma baseline"
- "Design expert annotation for dominant-seventh errors"
- "Measure whether detector disagreement predicts tutor uncertainty"
- "Create a blinded rubric for tutoring correctness and actionability"

The aim is to make HorizonJam a system other researchers can reproduce, challenge, and extend rather than a closed demonstration with impressive outputs but unclear evidence.