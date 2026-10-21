# Reproduction profiles

## Contract and browser checks

Use a fresh Python 3.13 environment and Node 22. From the repository root:

```powershell
python -m venv .venv-readiness
.venv-readiness/Scripts/python -m pip install -r requirements-ci.lock
.venv-readiness/Scripts/python -m pip check
npm ci
.venv-readiness/Scripts/python -m unittest discover -s tests -t . -v
.venv-readiness/Scripts/python -m playwright install chromium
.venv-readiness/Scripts/python eval/browser_runtime_check.py --output eval/readiness/my-browser-run.json
npm exec --offline next -- build ./nextjs-frontend
```

The browser evaluator owns localhost ports 3000/8001 and refuses to replace existing services. It uses real upload/WebSocket/browser recording code, synthetic microphone input, and deterministic substitutes for perception/model calls. It makes no provider calls. Every output path must be new; failed runs are retained too. Windows test execution needs permission to create/read/delete its isolated temporary directories.

Discover `tests/` explicitly. Root `test_moshi.py` is an optional manual model demo that imports PyTorch; root-level discovery imported it and failed in the clean contract environment. It is not part of the active contract suite. Do not add a large optional model dependency to hide that distinction.

`requirements-ci.txt` declares direct pins; `requirements-ci.lock` pins the complete installed Windows/Python 3.13 test environment. The lock does not include wheel hashes and is not a security-audited dependency set or proof of runtime inference. `.github/workflows/contract-checks.yml` must actually run successfully before remote CI is described as verified.

## Full detector/runtime environment: unresolved gate

The existing local Python 3.13 environment runs BasicPitch 0.4.0 with ONNX Runtime 1.22.0. Installed BasicPitch metadata requires TensorFlow <2.15.1 for Python >=3.11 on Windows; that is incompatible with a normal Python 3.13 dependency resolution. Do not silently install with `--no-deps` and call the environment reproducible.

Next step: select and validate a supported runtime Python/backend combination, or maintain an explicitly documented ONNX packaging solution in isolation. Preserve model/note/event equivalence checks and frozen detector results before changing the runtime. Generate a transitive dependency lock and complete a fresh real-WAV run on that profile before closing P0/P4. External direct-chord adapters remain in their existing isolated research environment.

## Baseline and report policy

`python eval/capture_execution_baseline.py --output <new-path.json>` captures hashes and installed package versions without collecting environment values, databases or audio. It refuses to overwrite a snapshot. The dirty worktree is recorded; the Git commit alone is not its identity. Preserve the source snapshot/commit separately before external reproduction.

Accepted research reports remain unchanged. New readiness evidence is under `eval/readiness`; it does not replace real-performance, expert, or learning-outcome evidence.
