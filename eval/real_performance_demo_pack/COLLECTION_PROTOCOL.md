# Real-performance pilot collection protocol

Status: collection preparation only. There are zero approved recordings. Twenty cases is the minimum pilot gate, not a claim of statistical adequacy or performer generalization.

## Recording task

Record 5-30 seconds of solo guitar. Start with a quiet room and an ordinary phone/laptop microphone. Keep the original file; do not denoise, trim, or retune without retaining the original and documenting preprocessing. Check permission before capturing another person's performance or background speech.

Collect chord-isolation and progression recordings across major/minor, dominant seventh, major seventh, minor seventh, sus2 and sus4. Include block chords, strumming, slow/fast arpeggios, inversions, partial voicings, and repeated transitions. Include modest noise, dynamics/tuning variation and multiple devices. The validator reports the exact missing coverage. Tag only conditions actually present.

Suggested progression tasks: I-IV-V-I, vi-IV-I-V, ii-V-I, i-iv-V-i, a secondary dominant, and a relative-major/minor ambiguous sequence. What the performer intended to play is task metadata, not the ground-truth annotation.

## Provenance and split assignment

1. Record OWNED/CONSENTED/LICENSED rights and an access-controlled rights reference; keep personal names/contact details and consent documents outside the repository.
2. Assign pseudonymous `performer_id`, `recording_session_id`, and `device_id`. Record SHA-256 and duration for each original audio file.
3. Group every performer and recording session into one split before viewing detector results. Do not split nearly identical takes to reach an exact fraction. Update the planned fractions before freezing if grouped assignment requires it.
4. Aim for multiple independent performers. A single-performer pilot can diagnose that performer's errors but cannot pass a performer-held-out generalization protocol.
5. Keep evaluation rights separate from permission to redistribute recordings.

## Annotation and freeze

Two distinct annotators independently listen without detector predictions and mark timed chord segments, confidence and ambiguity. Retain both annotations and report their disagreement; document adjudication before scoring. Do not silently choose the annotation that agrees with the detector. Do not treat unresolvable ambiguity as an unequivocal error or success.

Segments must be sorted, non-overlapping, positive-duration and within the recording. The manifest uses existing chord-label conventions. No label may be inferred merely from the collection task.

After independent review, calculate `eval.real_performance_pack.held_out_digest(cases)` over the frozen cases, record the actual UTC freeze time and digest, and restrict access to held-out labels during development. The validator recomputes the digest and rejects cross-split performer/session/audio duplication. A digest records identity; it does not establish rights or label correctness.

## Study decisions still needed before confirmation

Freeze primary chord metric, asserted accuracy AND abstention coverage, unsupported-tutor-claim ceiling, actionability rubric, model repetitions/settings, exclusions, and independent unit of analysis. Use pilot variability to determine a larger sample and minimum meaningful effect. For tutor review, blind evaluators to condition and randomize hard-label, summary, and summary+verification outputs from the same recordings.

Report all failures and ambiguous cases. If pilot/held-out results inform changes, obtain fresh confirmation recordings. Publish a negative result when appropriate; do not weaken a gate to promote a feature.
