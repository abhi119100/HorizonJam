"""Isolated local-file-only LV-Chordia JSON runner."""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import urllib.request
from pathlib import Path
from time import perf_counter


RESULT_PREFIX = "HORIZONJAM_LV_RESULT="


def _network_disabled(*_args, **_kwargs):
    raise RuntimeError("network access is disabled in the HorizonJam LV-Chordia runner")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument(
        "--chord-dict", default="submission", choices=("submission", "ismir2017", "full")
    )
    args = parser.parse_args()
    if "://" in args.input:
        raise ValueError("only local audio files are allowed")
    audio = Path(args.input).resolve()
    if not audio.is_file():
        raise FileNotFoundError(audio)

    urllib.request.urlopen = _network_disabled
    urllib.request.urlretrieve = _network_disabled
    os.environ.setdefault(
        "NUMBA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "horizonjam-numba-cache")
    )
    import_started = perf_counter()
    from lv_chordia.chord_recognition import chord_recognition
    import_sec = perf_counter() - import_started

    inference_started = perf_counter()
    raw_events = chord_recognition(str(audio), args.chord_dict)
    inference_sec = perf_counter() - inference_started
    events = [
        {
            "start": float(item["start_time"]),
            "end": float(item["end_time"]),
            "raw_label": str(item["chord"]),
            "score": None,
            "alternatives": [],
            "source": "lv_chordia",
        }
        for item in raw_events
        if float(item["end_time"]) > float(item["start_time"])
    ]
    payload = {
        "detector": "lv_chordia",
        "events": events,
        "warnings": [],
        "runtime": {
            "import_sec": import_sec,
            "inference_sec": inference_sec,
            "total_sec": import_sec + inference_sec,
        },
        "metadata": {
            "package_version": "1.1.0",
            "chord_dictionary": args.chord_dict,
            "device": "cpu",
            "upstream_url_handlers_disabled": True,
            "distribution_status": "RESEARCH_ONLY",
        },
    }
    print(RESULT_PREFIX + json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"LV-Chordia runner error: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
