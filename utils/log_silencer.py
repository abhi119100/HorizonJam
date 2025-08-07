#!/usr/bin/env python3
"""
Log silencer utility to reduce noise from third-party libraries
while preserving important error messages and debug information.
"""

import warnings
import logging
import os
from contextlib import contextmanager


def setup_noise_shield():
    """
    Set up comprehensive noise filtering for cleaner console output.
    Can be disabled by setting CHORDAI_DEBUG environment variable.
    """
    # Skip if debug mode is enabled
    if os.getenv("CHORDAI_DEBUG"):
        return
    
    # 1. Filter specific warning patterns
    warnings.filterwarnings(
        "ignore",
        message=r".*deprecated.*pkg_resources.*",   # pretty_midi / setuptools
    )
    warnings.filterwarnings(
        "ignore",
        message=r".*is too large for input signal.*",  # small-signal librosa warning
    )
    warnings.filterwarnings(
        "ignore",
        message=r".*Coremltools is not installed.*",   # basic-pitch optional deps
    )
    warnings.filterwarnings(
        "ignore",
        category=UserWarning,                          # catch-all UserWarnings
    )
    
    # 2. Set logging levels to ERROR for noisy libraries
    logging.basicConfig(level=logging.ERROR)
    noisy_loggers = [
        "chromadb", "httpx", "urllib3", "asyncio",         # network libs
        "matplotlib", "numba", "markdown",                 # misc
        "pretty_midi", "librosa", "tflite_runtime",        # audio stack
        "tensorflow", "basic_pitch"
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
    
    # 3. Set TensorFlow/TFLite environment variables
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # tensorflow / tflite
    os.environ["PYTHONWARNINGS"] = "ignore::UserWarning"


@contextmanager
def muted_warnings():
    """
    Context manager for temporarily silencing all warnings.
    Useful for wrapping particularly noisy function calls.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield


def filter_subprocess_output(output_lines):
    """
    Filter subprocess output to keep only relevant information.
    
    Args:
        output_lines (list): List of output lines from subprocess
        
    Returns:
        list: Filtered lines containing only relevant information
    """
    wanted = []
    for line in output_lines:
        # Keep HorizonJam section headers and important tags
        if (
            line.startswith("[BEAT_GRID]")
            or line.startswith("[KEY]")
            or line.startswith("[ONSET]")
            or line.startswith("Progression:")
            or line.startswith("🎵")
            or line.startswith("🎼")
            or line.startswith("🎹")
            or line.startswith("🎯")
            or line.startswith("📊")
            or "CHORD EVENT DETECTION" in line
            or "===" in line
            or line.strip().startswith("Total Chords:")
            or line.strip().startswith("Key:")
            or line.strip().startswith("Accuracy:")
        ):
            wanted.append(line)
    return wanted


# Auto-setup when imported (unless debug mode)
setup_noise_shield()