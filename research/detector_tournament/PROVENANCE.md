# Technology and Dataset Provenance Register

Audit date: 2026-08-30. This is an engineering screen, not legal advice.

| Item | Primary source | Recorded finding | Open gate |
|---|---|---|---|
| BasicPitch | https://github.com/spotify/basic-pitch | Apache-2.0; API returns model output, MIDI, and note events; upstream compatibility lists Python through 3.11 | identify bundled ONNX artifact notices and preserve version/hash |
| LV-Chordia | https://github.com/openmirlab/lv-chordia | repository claims MIT, bundled five-model ensemble, offline local inference, optional URL ingestion | inspect all files, bundled checkpoints, original-model lineage, dependency licenses, and wheel hashes |
| BTC | https://github.com/jayg996/BTC-ISMIR19 | MIT source; old dependency floor; README does not establish a distributable pretrained checkpoint | locate and audit exact weights before execution |
| CREMA | https://github.com/bmcfee/crema | source repository exposes direct file/array analysis; license metadata is inconsistent between repository summary and setup metadata | reconcile license and packaged pretrained-model rights; establish compatible legacy environment |
| NNLS Chroma/Chordino | https://github.com/c4dm/nnls-chroma | GPL-2.0-or-later Vamp plugin | research execution and distribution review |
| Librosa chroma | https://librosa.org/doc/0.11.0/generated/librosa.feature.chroma_cqt.html | current v3 dependency exposes CQT chroma | record exact library license/version and fixed parameters in executable wave |
| Essentia | https://github.com/MTG/essentia/blob/master/Essentia%20Licensing.txt | default AGPL-3.0-or-later terms | exclude from product unless licensing decision is explicit |
| Beat This | https://github.com/CPJKU/beat_this | MIT code/published weights; checkpoint download; training-data caveat | hash selected model and avoid evaluation leakage |
| Demucs | https://github.com/facebookresearch/demucs | MIT code repository archived in 2025 and no longer actively maintained | separate model-weight rights and mixed-song value audit |
| ShazamKit | https://developer.apple.com/shazamkit/ | official song/custom-catalog matching and time alignment across Apple platforms and Android | Apple service terms, credentials, privacy, catalog/reference rights; Mode B only |
| GuitarSet | https://github.com/marl/GuitarSet | repository is MIT; associated paper states CC BY 4.0 | verify actual audio/annotation host terms before download or redistribution |
| `mir_eval` | https://github.com/mir-evaluation/mir_eval | established chord and segmentation metric implementation | freeze version and label-conversion policy |

No external source, package, checkpoint, or dataset has been copied into the
repository. Before acquisition, add exact version/commit, license text hash,
artifact URL, SHA-256, size, network behavior, and redistribution decision.
