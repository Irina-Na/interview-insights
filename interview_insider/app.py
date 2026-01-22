from __future__ import annotations

from pathlib import Path
import json
import sys

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from interview_insider.qa_extractor import (  # noqa: E402
    extract_resume_text_from_bytes,
    run_qa_extraction,
    run_qa_extraction_for_file,
)
from interview_insider.qa_markdown_exporter import qa_json_to_markdown  # noqa: E402


LLM_MODELS = ["5.2", "4.1", "o4-mini", "o3"]
QA_OUTPUT_DIR = REPO_ROOT / "interview_insider" / "interview_insights"

QA_PROGRESS_STAGES = [
    "Проверка входных данных",
    "Извлечение текста из резюме",
    "Чтение транскриптов",
    "Подготовка контекста для LLM",
    "Запрос к модели (LLM)",
    "Пост-обработка/нормализация результата",
    "Сохранение файлов",
]


st.set_page_config(page_title="Interview Insights (QA only)", page_icon="I", layout="wide")
st.title("Interview Insights (QA only)")
st.markdown("Upload transcripts or provide a path; no transcription step.")

with st.sidebar:
    st.header("LLM settings")
    model = st.selectbox("Model", LLM_MODELS, index=2)
    language = st.text_input("Answer language", value="ru")
    vacancy = st.text_input("Vacancy name", value="")
    resume_file = st.file_uploader(
        "Resume (pdf/txt/md, optional)",
        type=["pdf", "txt", "md"],
    )

st.subheader("Transcripts")
transcript_files = st.file_uploader(
    "Transcript TXT files",
    type=["txt"],
    accept_multiple_files=True,
)
transcript_path_input = st.text_input(
    "Or path to a transcript file/folder",
    value="",
)

st.markdown(
    "**Стадии извлечения:**\n"
    + "\n".join(f"- {stage}" for stage in QA_PROGRESS_STAGES)
)

if st.button("Extract QA"):
    stage_text = st.empty()
    progress_bar = st.progress(0, text="Готовимся к извлечению QA...")

    def set_stage(stage_index: int, detail: str = "") -> None:
        stage_label = QA_PROGRESS_STAGES[stage_index]
        if detail:
            stage_label = f"{stage_label} — {detail}"
        progress_value = int((stage_index / len(QA_PROGRESS_STAGES)) * 100)
        progress_bar.progress(progress_value, text=stage_label)
        stage_text.caption(stage_label)

    set_stage(0)
    QA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not transcript_files and not transcript_path_input:
        st.warning("Upload files or provide a path.")
        progress_bar.progress(0, text="Нужны транскрипты для старта.")
        stage_text.empty()
        st.stop()

    resume_text: str | None = None
    set_stage(1)
    if resume_file is not None:
        resume_text = extract_resume_text_from_bytes(
            resume_file.getvalue(),
            Path(resume_file.name).suffix,
        )
    else:
        stage_text.caption("Извлечение текста из резюме — резюме не загружено")

    if transcript_files:
        set_stage(2, f"файлов: {len(transcript_files)}")
        file_progress = st.progress(0, text="Подготовка транскриптов...")
        for index, transcript in enumerate(transcript_files, start=1):
            transcript_text = transcript.getvalue().decode("utf-8", errors="ignore").strip()
            if not transcript_text:
                continue
            set_stage(3, transcript.name)
            set_stage(4, transcript.name)
            run_qa_extraction(
                transcript_text=transcript_text,
                resume_text=resume_text,
                model=model,
                vacancy=vacancy or None,
                language=language,
                output_dir=QA_OUTPUT_DIR,
                output_name=f"{Path(transcript.name).stem}_qa.json",
            )
            set_stage(5, transcript.name)
            set_stage(6, transcript.name)
            file_progress.progress(
                min(100, int(index / len(transcript_files) * 100)),
                text=f"Обработано: {transcript.name}",
            )
        progress_bar.progress(100, text="Готово")
        st.success(f"Done. QA saved to {QA_OUTPUT_DIR}.")
    elif transcript_path_input:
        input_path = Path(transcript_path_input)
        if input_path.is_file():
            set_stage(2, input_path.name)
            set_stage(3, input_path.name)
            set_stage(4, input_path.name)
            run_qa_extraction_for_file(
                transcript_path=input_path,
                resume_text=resume_text,
                model=model,
                vacancy=vacancy or None,
                language=language,
                output_dir=QA_OUTPUT_DIR,
            )
            set_stage(5, input_path.name)
            set_stage(6, input_path.name)
            progress_bar.progress(100, text="Готово")
            st.success(f"Done. QA saved to {QA_OUTPUT_DIR}.")
        elif input_path.is_dir():
            transcript_paths = sorted(input_path.glob("*.txt"))
            if not transcript_paths:
                st.warning("No .txt files found in the folder.")
            else:
                set_stage(2, f"файлов: {len(transcript_paths)}")
                file_progress = st.progress(0, text="Подготовка транскриптов...")
                for index, transcript_path in enumerate(transcript_paths, start=1):
                    set_stage(3, transcript_path.name)
                    set_stage(4, transcript_path.name)
                    run_qa_extraction_for_file(
                        transcript_path=transcript_path,
                        resume_text=resume_text,
                        model=model,
                        vacancy=vacancy or None,
                        language=language,
                        output_dir=QA_OUTPUT_DIR,
                    )
                    set_stage(5, transcript_path.name)
                    set_stage(6, transcript_path.name)
                    file_progress.progress(
                        min(
                            100,
                            int(index / len(transcript_paths) * 100),
                        ),
                        text=f"Обработано: {transcript_path.name}",
                    )
                progress_bar.progress(100, text="Готово")
                st.success(f"Done. QA saved to {QA_OUTPUT_DIR}.")
        else:
            st.warning("Path not found.")

st.divider()
st.subheader("Saved QA outputs")
if not QA_OUTPUT_DIR.exists():
    st.info("No QA JSON files yet.")
else:
    qa_files = sorted(
        QA_OUTPUT_DIR.glob("*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not qa_files:
        st.info("No QA JSON files yet.")
    else:
        selected_file = st.selectbox(
            "Select a QA JSON file",
            qa_files,
            format_func=lambda path: path.name,
        )
        if selected_file:
            try:
                qa_data = json.loads(selected_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                st.error(f"Failed to read {selected_file.name}: {exc}")
            else:
                st.markdown(qa_json_to_markdown(qa_data))
