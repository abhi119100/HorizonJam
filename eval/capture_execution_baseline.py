"""Capture source/report hashes without collecting secrets or rewriting evidence."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def capture() -> dict:
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
    ).decode("utf-8").split("\0")
    hashes = {}
    for name in sorted(set(names)):
        path = ROOT / name
        if not name or not path.is_file() or path.is_symlink():
            continue
        if any(part in {"_archive", "RAG", "node_modules", ".git", "readiness"} for part in Path(name).parts):
            continue
        if path.suffix not in {".py", ".js", ".md", ".json", ".toml", ".lock"} and name != "requirements.txt":
            continue
        if path.name.startswith(".env"):
            continue
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    packages = {}
    for name in ("fastapi", "starlette", "uvicorn", "python-multipart", "httpx", "numpy", "scipy", "soundfile", "librosa", "basic-pitch", "onnxruntime", "pretty_midi", "music21", "chromadb", "openai", "aiohttp", "playwright"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "schema_version": "execution-baseline-v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "worktree": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True).splitlines(),
        "python": platform.python_version(), "platform": platform.platform(),
        "packages": packages, "sha256": hashes,
        "limitations": ["Hashes preserve identity, not a source archive.", "Existing dirty/untracked work is included; commit alone is insufficient to reproduce it.", "No environment values, database contents, private audio, or credentials collected.", "A local installed-version inventory is not a clean-install dependency lock."],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = capture()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"Captured {len(report['sha256'])} hashes; existing reports unchanged.")
