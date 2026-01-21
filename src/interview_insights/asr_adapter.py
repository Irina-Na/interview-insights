from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


SPEECH_TO_TEXT_DIR = Path(__file__).resolve().parent.parent.parent / "speech-to-text"


def add_speech_to_text_to_path() -> Path:
    """Ensure the speech-to-text submodule is on sys.path.

    Returns the submodule path so callers can reuse it.
    """
    if SPEECH_TO_TEXT_DIR.exists():
        path_str = str(SPEECH_TO_TEXT_DIR)
        if path_str not in sys.path:
            sys.path.append(path_str)
    else:
        raise FileNotFoundError(
            f"Expected speech-to-text submodule at {SPEECH_TO_TEXT_DIR}, but it is missing."
        )
    return SPEECH_TO_TEXT_DIR


def run_batch_transcribe(**kwargs: Any) -> None:
    """Thin wrapper around speech-to-text's batch_transcribe.

    Usage:
        run_batch_transcribe(input_dir=Path("video"), output_dir=Path("outputs"), model_size="medium")
    """
    add_speech_to_text_to_path()
    try:
        from batch_transcribe import batch_transcribe  # type: ignore
    except Exception as exc:  # pragma: no cover - defensive import
        raise RuntimeError(
            "Cannot import batch_transcribe from the speech-to-text submodule."
        ) from exc

    batch_transcribe(**kwargs)


__all__ = [
    "add_speech_to_text_to_path",
    "run_batch_transcribe",
]