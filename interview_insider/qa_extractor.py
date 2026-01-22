from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from interview_insider.llm_client import LLMClient
from interview_insider.prompts.extracton_models_and_prompts import prompt_QA_extractor


def build_system_prompt(*, vacancy: str | None, language: str = "english") -> str:
    return prompt_QA_extractor.format(
        vacancy=vacancy or "unknown",
        language=language,
    )


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp1251")


def _extract_pdf_text(stream: BytesIO) -> str:
    reader = PdfReader(stream)
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages).strip()


def extract_resume_text_from_file(path: Path | None) -> str | None:
    if not path:
        return None
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {path}")

    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return _read_text_file(path).strip()
    if suffix == ".pdf":
        with path.open("rb") as file_handle:
            return _extract_pdf_text(BytesIO(file_handle.read()))
    raise ValueError(f"Unsupported resume format: {suffix}")


def extract_resume_text_from_bytes(data: bytes, suffix: str) -> str:
    suffix = suffix.lower()
    if suffix in {".txt", ".md"}:
        return data.decode("utf-8", errors="ignore").strip()
    if suffix == ".pdf":
        return _extract_pdf_text(BytesIO(data))
    raise ValueError(f"Unsupported resume format: {suffix}")


def _collect_transcript_files(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted([p for p in path.iterdir() if p.suffix.lower() == ".txt"])
    return [path]


def _default_output_name(source_path: Path) -> str:
    return f"{source_path.stem}_qa.json"


def run_qa_extraction(
    *,
    transcript_text: str,
    resume_text: str | None = None,
    model: str,
    vacancy: str | None = None,
    language: str = "ru",
    output_dir: str | Path = "interview_insider/interview_insights",
    output_name: str | None = None,
) -> Path:
    system_prompt = build_system_prompt(vacancy=vacancy, language=language)
    user_message = (
        f"#RESUME: {resume_text or ''}\n"
        f"#INTERVIEW TRANSCRIPTION: {transcript_text}"
    )
    llm_client = LLMClient()
    result_json = llm_client.extract_qa_json(
        system_prompt=system_prompt,
        user_message=user_message,
        model=model,
    )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if output_name:
        filename = output_name
        if not filename.lower().endswith(".json"):
            filename = f"{filename}.json"
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"qa_extraction_{timestamp}.json"

    file_path = output_path / filename
    file_path.write_text(
        json.dumps(result_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return file_path


def run_qa_extraction_for_file(
    *,
    transcript_path: Path,
    resume_text: str | None,
    model: str,
    vacancy: str | None,
    language: str,
    output_dir: str | Path,
) -> Path:
    transcript_text = _read_text_file(transcript_path).strip()
    if not transcript_text:
        raise ValueError(f"Transcript is empty: {transcript_path}")
    return run_qa_extraction(
        transcript_text=transcript_text,
        resume_text=resume_text,
        model=model,
        vacancy=vacancy,
        language=language,
        output_dir=output_dir,
        output_name=_default_output_name(transcript_path),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract QA pairs from transcript file(s) and save JSON outputs."
    )
    parser.add_argument(
        "--vacancy",
        default=None,
        help="Vacancy or position name.",
    )
    parser.add_argument(
        "--resume",
        type=Path,
        default=None,
        help="Path to resume file (.pdf/.txt/.md).",
    )
    parser.add_argument(
        "--language",
        default="ru",
        help="Language for the output (default: ru).",
    )
    parser.add_argument(
        "--model",
        required=True,
        choices=["5.2", "4.1", "o4-mini", "o3"],
        help="LLM model alias.",
    )
    parser.add_argument(
        "--transcript",
        type=Path,
        required=True,
        help="Path to transcript file or directory with .txt files.",
    )
    parser.add_argument(
        "--output-dir",
        default="interview_insider/interview_insights",
        help="Directory for QA JSON outputs.",
    )
    args = parser.parse_args()

    resume_text = extract_resume_text_from_file(args.resume)
    transcript_files = _collect_transcript_files(args.transcript)
    if not transcript_files:
        raise FileNotFoundError(f"No transcript files found in {args.transcript}")

    for transcript_path in transcript_files:
        run_qa_extraction_for_file(
            transcript_path=transcript_path,
            resume_text=resume_text,
            model=args.model,
            vacancy=args.vacancy,
            language=args.language,
            output_dir=args.output_dir,
        )


if __name__ == "__main__":
    main()
