# Product Evidence UX v1

## Summary rules

- `STRONG_AGREEMENT`: symbolic and DSP canonical chord agree with no warnings.
- `PARTIAL_AGREEMENT`: same root, or exact agreement affected by warnings.
- `MIXED_EVIDENCE`: symbolic and DSP canonical roots disagree.
- `LIMITED_EVIDENCE`: independent DSP candidate unavailable.

## Tutor behavior

Fixed context cases: 3. Summary propagation: 3/3. Uncertainty behavior: 3/3.
Mixed/limited hard-label assertions repaired: 2/2. Raw-evidence exposure cases: 0.
Mean prompt growth: 602 characters.

This is deterministic assembly/verification evidence, not a provider-model or teaching-effect result.

## UI behavior

The progression view contains a collapsed `Why this chord?` disclosure with categorical strength, musical wording, and observed pitch-class names. It never shows vectors, scores, paths, or internal weights.

Feedback choices are Correct chord, Wrong chord, and Not sure. The browser retains at most 50 compact local records under a random session identifier. Audio, filenames, paths, and corrections are not uploaded or retained.

## Limitations

- No provider model was used; this evaluates deterministic context and verification behavior.
- No learning, pedagogy, accuracy, or calibrated-confidence improvement is claimed.
- EvidenceSummary categories are fixed rules and require real-performance validation.
