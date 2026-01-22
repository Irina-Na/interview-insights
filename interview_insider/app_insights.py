from __future__ import annotations

from pathlib import Path
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


LLM_MODELS = ["5.2", "4.1", "o4-mini", "o3"]
QA_OUTPUT_DIR = REPO_ROOT / "interview_insider" / "interview_insights"


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

resume_text: str | None = None
if resume_file is not None:
    resume_text = extract_resume_text_from_bytes(
        resume_file.getvalue(),
        Path(resume_file.name).suffix,
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

if st.button("Extract QA"):
    QA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if transcript_files:
        for transcript in transcript_files:
            transcript_text = transcript.getvalue().decode("utf-8", errors="ignore").strip()
            if not transcript_text:
                continue
            run_qa_extraction(
                transcript_text=transcript_text,
                resume_text=resume_text,
                model=model,
                vacancy=vacancy or None,
                language=language,
                output_dir=QA_OUTPUT_DIR,
                output_name=f"{Path(transcript.name).stem}_qa.json",
            )
        st.success(f"Done. QA saved to {QA_OUTPUT_DIR}.")
    elif transcript_path_input:
        input_path = Path(transcript_path_input)
        if input_path.is_file():
            run_qa_extraction_for_file(
                transcript_path=input_path,
                resume_text=resume_text,
                model=model,
                vacancy=vacancy or None,
                language=language,
                output_dir=QA_OUTPUT_DIR,
            )
            st.success(f"Done. QA saved to {QA_OUTPUT_DIR}.")
        elif input_path.is_dir():
            transcript_paths = sorted(input_path.glob("*.txt"))
            if not transcript_paths:
                st.warning("No .txt files found in the folder.")
            else:
                for transcript_path in transcript_paths:
                    run_qa_extraction_for_file(
                        transcript_path=transcript_path,
                        resume_text=resume_text,
                        model=model,
                        vacancy=vacancy or None,
                        language=language,
                        output_dir=QA_OUTPUT_DIR,
                    )
                st.success(f"Done. QA saved to {QA_OUTPUT_DIR}.")
        else:
            st.warning("Path not found.")
    else:
        st.warning("Upload files or provide a path.")
