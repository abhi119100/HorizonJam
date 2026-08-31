# Environment Isolation Plan

## Rules

- Never install a tournament candidate into the HorizonJam v3 environment.
- Give each candidate its own locked virtual environment or container.
- Run adapters as subprocesses exchanging versioned JSON and content-addressed
  artifacts; do not import candidate modules into the product process.
- Pin source commits, package hashes, transitive dependencies, model URLs,
  model hashes, and accepted licenses before execution.
- Download only during an explicit acquisition step. Benchmark inference runs
  with network access disabled.
- Reject URL inputs and shell interpolation in adapters.
- Store no credentials in configs, reports, command lines, or model caches.
- Bound wall time, memory, output size, and accessible input/output paths.

## Proposed Environments

| Environment | Purpose | Initial policy |
|---|---|---|
| `hj-v3-baseline` | frozen current detectors | existing environment, read-only comparison |
| `hj-research-dsp` | Librosa CQT/chroma | minimal lock based on current compatible versions |
| `hj-research-lvchordia` | LV-Chordia | separate Python/PyTorch lock; local files only |
| `hj-research-btc` | original/maintained BTC audit | create only after checkpoint provenance is resolved |
| `hj-research-crema` | legacy TensorFlow baseline | container/older Python only; never share site-packages |
| `hj-research-native` | Chordino/Vamp | container or standalone executable boundary |
| `hj-research-beats` | Beat This | deferred until segmentation experiment |

Environment creation and model acquisition are separate reviewed actions. This
first pass creates neither.
