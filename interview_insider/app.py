from __future__ import annotations

from pathlib import Path
from typing import Any
import html
from typing import Any
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


LLM_MODELS = ["o3", "5.2", "4.1", "o4-mini"]
QA_OUTPUT_DIR = REPO_ROOT / "interview_insider" / "interview_insights"
MODEL_CARDS = [
    {
        "name": "o3",
        "summary": "Reasoning model for complex tasks.",
        "tagline": "Reasoning first",
        "reasoning": "5/5",
        "speed": "1/3",
        "reasoning_supported": True,
        "reasoning_tokens": True,
        "theme": "sunset",
        "pricing": {
            "input": "$2.00",
            "cached_input": "$0.50",
            "output": "$8.00",
        },
    },
    {
        "name": "5.2",
        "summary": "Best for coding and agentic tasks.",
        "tagline": "Agentic coding",
        "reasoning": "5/5",
        "speed": "3/3",
        "reasoning_supported": True,
        "reasoning_tokens": True,
        "theme": "ocean",
        "pricing": {
            "input": "$1.75",
            "cached_input": "$0.18",
            "output": "$14.00",
        },
    },
    {
        "name": "o4-mini",
        "summary": "Fast, cost-efficient reasoning model.",
        "tagline": "Fast + efficient",
        "reasoning": "4/5",
        "speed": "3/3",
        "reasoning_supported": True,
        "reasoning_tokens": True,
        "theme": "dawn",
        "pricing": {
            "input": "$1.10",
            "cached_input": "$0.28",
            "output": "$4.40",
        },
    },
    {
        "name": "4.1",
        "summary": "Strongest non-reasoning model.",
        "tagline": "Pure intelligence",
        "intelligence": "4/5",
        "speed": "3/3",
        "reasoning_supported": False,
        "reasoning_tokens": False,
        "theme": "cloud",
        "pricing": {
            "input": "$2.00",
            "cached_input": "$0.50",
            "output": "$8.00",
        },
    },
]

QA_PROGRESS_STAGES = [
    "Validating input data",
    "Extracting resume text",
    "Reading transcripts",
    "Preparing context for the LLM",
    "Querying the model (LLM)",
    "Post-processing / normalization",
    "Saving output files",
]
QA_PROGRESS_INDEX = {stage: idx for idx, stage in enumerate(QA_PROGRESS_STAGES)}


def _extract_usage_numbers(usage: dict) -> dict[str, int]:
    if not isinstance(usage, dict):
        return {}
    summary: dict[str, int] = {}
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    total_tokens = usage.get("total_tokens")
    if isinstance(input_tokens, int):
        summary["input_tokens"] = input_tokens
    if isinstance(output_tokens, int):
        summary["output_tokens"] = output_tokens
    if isinstance(total_tokens, int):
        summary["total_tokens"] = total_tokens
    input_details = usage.get("input_tokens_details") or {}
    output_details = usage.get("output_tokens_details") or {}
    cached_tokens = input_details.get("cached_tokens")
    reasoning_tokens = output_details.get("reasoning_tokens")
    if isinstance(cached_tokens, int):
        summary["cached_input_tokens"] = cached_tokens
    if isinstance(reasoning_tokens, int):
        summary["reasoning_tokens"] = reasoning_tokens
    return summary


st.set_page_config(page_title="Interview Insights (QA only)", page_icon="I", layout="wide")
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap');

      :root {
        --bg: #0f1116;
        --surface: #171a21;
        --surface-strong: #1f2430;
        --text: #f3f5f9;
        --muted: #9aa3b2;
        --line: rgba(255,255,255,0.08);
        --accent: #8be2ff;
      }

      .stApp {
        background:
          radial-gradient(1200px 520px at 15% -10%, rgba(98, 180, 255, 0.16), transparent 60%),
          radial-gradient(900px 420px at 90% 0%, rgba(255, 199, 122, 0.12), transparent 55%),
          var(--bg);
        color: var(--text);
        font-family: 'Plus Jakarta Sans', sans-serif;
      }

      h1, h2, h3, .section-title {
        font-family: 'Space Grotesk', sans-serif;
        letter-spacing: -0.02em;
      }

      .section-title {
        font-size: 1.6rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
      }

      .hero-subtitle {
        color: var(--muted);
        margin-top: -0.4rem;
      }

      .model-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
        border: 1px solid var(--line);
        border-radius: 22px;
        padding: 0;
        overflow: hidden;
        box-shadow: 0 20px 40px rgba(0,0,0,0.35);
      }

      .model-card-inner {
        padding: 1.2rem 1.4rem 1.4rem 1.4rem;
      }

      .model-hero {
        height: 120px;
        border-radius: 18px;
        margin: 1.1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: #0b0d12;
      }

      .theme-sunset {
        background: radial-gradient(circle at top left, #ffd36a, #a1b8ff 70%);
      }
      .theme-ocean {
        background: radial-gradient(circle at top left, #02d8ff, #4d6bff 70%);
      }
      .theme-dawn {
        background: radial-gradient(circle at top left, #f7c7a6, #9fd4ff 70%);
      }
      .theme-cloud {
        background: radial-gradient(circle at top left, #d7e3f3, #f5c0dd 70%);
      }

      .model-meta {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.6rem;
      }

      .model-tagline {
        color: var(--muted);
        font-size: 0.92rem;
      }

      .badge {
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        font-size: 0.75rem;
        color: #0b0d12;
        background: var(--accent);
        font-weight: 600;
      }

      .model-summary {
        color: var(--text);
        margin-bottom: 1rem;
        line-height: 1.4;
      }

      .rating-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-top: 1px solid var(--line);
        padding: 0.6rem 0;
      }

      .rating-row:first-child {
        border-top: none;
      }

      .rating-label {
        color: var(--muted);
        font-size: 0.88rem;
      }

      .rating-stars {
        font-size: 0.9rem;
        letter-spacing: 0.12em;
      }

      .pricing {
        margin-top: 1rem;
        background: var(--surface);
        border-radius: 14px;
        padding: 0.9rem 1rem;
        border: 1px solid var(--line);
      }

      .pricing-header {
        display: flex;
        justify-content: space-between;
        font-size: 0.75rem;
        text-transform: uppercase;
        color: var(--muted);
        letter-spacing: 0.08em;
      }

      .pricing-row {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-top: 1px solid var(--line);
        font-size: 0.92rem;
      }

      .pricing-row:first-of-type {
        border-top: none;
        margin-top: 0.4rem;
      }

      .pill {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.08);
        font-size: 0.78rem;
        color: var(--text);
      }

      .qa-card {
        border-top: 1px solid var(--line);
        padding: 1.4rem 0 1.6rem 0;
      }

      .qa-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.45rem;
        font-weight: 600;
        margin-bottom: 0.4rem;
      }

      .qa-meta {
        color: var(--muted);
        font-size: 0.95rem;
        margin: 0.1rem 0;
      }

      .qa-section {
        margin-top: 1rem;
      }

      .qa-section-title {
        font-weight: 600;
        margin-bottom: 0.4rem;
      }

      .qa-list {
        padding-left: 1.2rem;
        margin: 0.2rem 0 0.2rem 0;
      }

      .qa-list li {
        margin: 0.2rem 0;
      }

      .qa-stages {
        margin: 0.1rem 0 0 0;
        padding-left: 1.05rem;
      }

      .qa-stages li {
        margin: 0.05rem 0;
      }

      .qa-error-icon {
        color: #ff6b6b;
        font-weight: 700;
        margin-right: 0.5rem;
      }

      .qa-quote {
        border-left: 2px solid rgba(255,255,255,0.2);
        padding-left: 0.9rem;
        margin: 0.5rem 0 0.2rem 0;
        color: var(--text);
      }

      .qa-label {
        font-weight: 600;
        color: var(--text);
      }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("Interview Insights (QA only)")
st.markdown("<p class='hero-subtitle'>Upload transcripts or provide a path; no transcription step.</p>", unsafe_allow_html=True)

with st.sidebar:
    st.header("LLM settings")
    model = st.selectbox("Model", LLM_MODELS, index=0)
    language = st.text_input("Answer language", value="ru")
    vacancy = st.text_input("Vacancy name", value="")
    resume_file = st.file_uploader(
        "Resume (pdf/txt/md, optional)",
        type=["pdf", "txt", "md"],
    )

st.markdown("<div class='section-title'>Model comparison</div>", unsafe_allow_html=True)


def render_card(card: dict[str, object]) -> str:
    pricing = card.get("pricing") or {}
    reasoning_supported = card.get("reasoning_supported")
    reasoning_tokens = card.get("reasoning_tokens")
    if reasoning_supported:
        badge_text = "Reasoning"
    else:
        badge_text = "Non-reasoning"

    reasoning_stars = card.get("reasoning")
    intelligence_stars = card.get("intelligence")
    speed_stars = card.get("speed")
    primary_label = "Reasoning" if reasoning_stars is not None else "Intelligence"
    primary_stars = reasoning_stars or intelligence_stars or ""

    return f"""
      <div class="model-card">
        <div class="model-hero theme-{card.get('theme', 'sunset')}">{card.get('name')}</div>
        <div class="model-card-inner">
          <div class="model-meta">
            <div class="model-tagline">{card.get('tagline')}</div>
            <span class="badge">{badge_text}</span>
          </div>
          <div class="model-summary">{card.get('summary')}</div>
          <div class="pill">Reasoning tokens: {"Yes" if reasoning_tokens else "No"}</div>
          <div class="rating-row">
            <span class="rating-label">{primary_label}</span>
            <div class="rating-stars">{primary_stars}</div>
          </div>
          <div class="rating-row">
            <span class="rating-label">Speed</span>
            <div class="rating-stars">{speed_stars}</div>
          </div>
          <div class="pricing">
            <div class="pricing-header">
              <span>Pricing</span>
              <span>Per 1M tokens</span>
            </div>
            <div class="pricing-row">
              <span>Input</span>
              <span>{pricing.get('input', '?')}</span>
            </div>
            <div class="pricing-row">
              <span>Cached input</span>
              <span>{pricing.get('cached_input', '?')}</span>
            </div>
            <div class="pricing-row">
              <span>Output</span>
              <span>{pricing.get('output', '?')}</span>
            </div>
          </div>
        </div>
      </div>
    """


def _render_bulleted_list(
    items: list[str],
    icon_html: str | None = None,
    list_class: str = "qa-list",
) -> str:
    li_items = []
    for item in items:
        safe_item = html.escape(str(item).strip())
        if not safe_item:
            continue
        prefix = icon_html or ""
        li_items.append(f"<li>{prefix}{safe_item}</li>")
    if not li_items:
        return ""
    return f"<ul class='{list_class}'>" + "".join(li_items) + "</ul>"


def _escape_with_breaks(text: str) -> str:
    return html.escape(text).replace("\n", "<br>")


def _render_qa_json_structured(qa_json: dict[str, Any]) -> None:
    vacancy = str(qa_json.get("vacancy") or "").strip()
    if vacancy:
        st.markdown(f"# Interview Insights - {vacancy}")
    else:
        st.markdown("# Interview Insights")

    role = str(qa_json.get("employee_role_identified") or "").strip()
    if role:
        st.markdown(f"**Role identified:** {role}")

    stages = qa_json.get("stages_of_conversation_short") or []
    if isinstance(stages, list) and stages:
        st.markdown("**Conversation stages:**")
        stages_list = _render_bulleted_list(
            stages,
            list_class="qa-list qa-stages",
        )
        if stages_list:
            st.markdown(stages_list, unsafe_allow_html=True)

    items = qa_json.get("items") or []
    if not isinstance(items, list):
        items = []

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue

        question = str(item.get("question") or "").strip()
        safe_question = html.escape(question)
        title = f"Q{index}. <em>{safe_question}</em>" if question else f"Q{index}"
        st.markdown(
            f"<div class='qa-card'><div class='qa-title'>{title}</div>",
            unsafe_allow_html=True,
        )

        timecode = str(item.get("timecode") or "").strip()
        place = str(item.get("place_in_the_text") or "").strip()
        if timecode:
            st.markdown(
                f"<div class='qa-meta'><span class='qa-label'>Timecode:</span> {html.escape(timecode)}</div>",
                unsafe_allow_html=True,
            )
        if place:
            st.markdown(
                f"<div class='qa-meta'><span class='qa-label'>Place:</span> {html.escape(place)}</div>",
                unsafe_allow_html=True,
            )

        candidate_answer = str(item.get("candidates_answer") or "").strip()
        if candidate_answer:
            st.markdown("<div class='qa-section'><div class='qa-section-title'>Candidate answer (summary):</div></div>", unsafe_allow_html=True)
            st.markdown(candidate_answer)

        short_eval = str(item.get("short_candidate_answer_evaluation") or "").strip()
        if short_eval:
            st.markdown("<div class='qa-section'><div class='qa-section-title'>Answer evaluation (short):</div></div>", unsafe_allow_html=True)
            st.markdown(short_eval)

        key_idea = str(item.get("key_idea") or "").strip()
        if key_idea:
            st.markdown("<div class='qa-section'><div class='qa-section-title'>Key idea:</div></div>", unsafe_allow_html=True)
            st.markdown(key_idea)

        errors = item.get("errors_and_problems") or []
        if isinstance(errors, list) and errors:
            errors_list = _render_bulleted_list(errors, "<span class='qa-error-icon'>x</span>")
            if errors_list:
                st.markdown("<div class='qa-section'><div class='qa-section-title'>Issues:</div></div>", unsafe_allow_html=True)
                st.markdown(errors_list, unsafe_allow_html=True)

        improvements = item.get("what_to_fix") or []
        if isinstance(improvements, list) and improvements:
            improvements_list = _render_bulleted_list(improvements)
            if improvements_list:
                st.markdown("<div class='qa-section'><div class='qa-section-title'>How to improve the answer:</div></div>", unsafe_allow_html=True)
                st.markdown(improvements_list, unsafe_allow_html=True)
        elif isinstance(improvements, str) and improvements.strip():
            st.markdown("<div class='qa-section'><div class='qa-section-title'>How to improve the answer:</div></div>", unsafe_allow_html=True)
            st.markdown(improvements.strip())

        ideal_ru = str(item.get("the_ideal_answer_example_ru") or "").strip()
        ideal_en = str(item.get("the_ideal_answer_example_eng") or "").strip()
        if ideal_ru or ideal_en:
            st.markdown("<div class='qa-section'><div class='qa-section-title'>Ideal answer:</div></div>", unsafe_allow_html=True)
            st.markdown("<div class='qa-label'>RU:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='qa-quote'>{_escape_with_breaks(ideal_ru or '--')}</div>", unsafe_allow_html=True)
            st.markdown("<div class='qa-label'>EN:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='qa-quote'>{_escape_with_breaks(ideal_en or '--')}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


model_columns = st.columns(len(MODEL_CARDS), gap="large")
for column, card in zip(model_columns, MODEL_CARDS):
    with column:
        st.markdown(render_card(card), unsafe_allow_html=True)

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
    "**Extraction stages:**\n"
    + "\n".join(f"- {stage}" for stage in QA_PROGRESS_STAGES)
)

if st.button("Extract QA"):
    stage_text = st.empty()
    stage_list = st.empty()
    progress_bar = st.progress(0, text="Preparing QA extraction...")

    def _render_stage_list(current_index: int) -> str:
        lines = ["**Extraction stages (live):**"]
        for idx, stage in enumerate(QA_PROGRESS_STAGES):
            if idx < current_index:
                marker = "x"
            elif idx == current_index:
                marker = ">"
            else:
                marker = " "
            lines.append(f"- [{marker}] {stage}")
        return "\n".join(lines)

    def set_stage(stage: int | str, detail: str = "") -> None:
        if isinstance(stage, int):
            stage_index = stage
            stage_label = QA_PROGRESS_STAGES[stage_index]
        else:
            stage_label = stage
            stage_index = QA_PROGRESS_INDEX.get(stage_label, 0)
        if detail:
            stage_label = f"{stage_label} - {detail}"
        progress_value = int(((stage_index + 1) / len(QA_PROGRESS_STAGES)) * 100)
        progress_bar.progress(min(100, progress_value), text=stage_label)
        stage_text.caption(stage_label)
        stage_list.markdown(_render_stage_list(stage_index))

    def stage_callback(stage_label: str, detail: str = "") -> None:
        set_stage(stage_label, detail)

    set_stage(0)
    QA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not transcript_files and not transcript_path_input:
        st.warning("Upload files or provide a path.")
        progress_bar.progress(0, text="Transcripts are required to start.")
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
        stage_text.caption("Skipping resume extraction - no resume uploaded.")

    if transcript_files:
        set_stage(2, f"files: {len(transcript_files)}")
        file_progress = None
        if len(transcript_files) > 1:
            file_progress = st.progress(0, text="Preparing transcripts...")
        for index, transcript in enumerate(transcript_files, start=1):
            set_stage(2, transcript.name)
            transcript_text = transcript.getvalue().decode("utf-8", errors="ignore").strip()
            if not transcript_text:
                continue
            file_stage_callback = lambda label, name=transcript.name: stage_callback(label, name)
            run_qa_extraction(
                transcript_text=transcript_text,
                resume_text=resume_text,
                model=model,
                vacancy=vacancy or None,
                language=language,
                output_dir=QA_OUTPUT_DIR,
                output_name=f"{Path(transcript.name).stem}_qa.json",
                stage_callback=file_stage_callback,
            )
            if file_progress is not None:
                file_progress.progress(
                    min(100, int(index / len(transcript_files) * 100)),
                    text=f"Processed: {transcript.name}",
                )
        progress_bar.progress(100, text="Done")
        st.success(f"Done. QA saved to {QA_OUTPUT_DIR}.")
    elif transcript_path_input:
        input_path = Path(transcript_path_input)
        if input_path.is_file():
            set_stage(2, input_path.name)
            file_stage_callback = lambda label, name=input_path.name: stage_callback(label, name)
            run_qa_extraction_for_file(
                transcript_path=input_path,
                resume_text=resume_text,
                model=model,
                vacancy=vacancy or None,
                language=language,
                output_dir=QA_OUTPUT_DIR,
                stage_callback=file_stage_callback,
            )
            progress_bar.progress(100, text="Done")
            st.success(f"Done. QA saved to {QA_OUTPUT_DIR}.")
        elif input_path.is_dir():
            transcript_paths = sorted(input_path.glob("*.txt"))
            if not transcript_paths:
                st.warning("No .txt files found in the folder.")
            else:
                set_stage(2, f"files: {len(transcript_paths)}")
                file_progress = None
                if len(transcript_paths) > 1:
                    file_progress = st.progress(0, text="Preparing transcripts...")
                for index, transcript_path in enumerate(transcript_paths, start=1):
                    set_stage(2, transcript_path.name)
                    file_stage_callback = lambda label, name=transcript_path.name: stage_callback(label, name)
                    run_qa_extraction_for_file(
                        transcript_path=transcript_path,
                        resume_text=resume_text,
                        model=model,
                        vacancy=vacancy or None,
                        language=language,
                        output_dir=QA_OUTPUT_DIR,
                        stage_callback=file_stage_callback,
                    )
                    if file_progress is not None:
                        file_progress.progress(
                            min(
                                100,
                                int(index / len(transcript_paths) * 100),
                            ),
                            text=f"Processed: {transcript_path.name}",
                        )
                progress_bar.progress(100, text="Done")
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
                usage_path = selected_file.with_suffix(".usage.json")
                if usage_path.exists():
                    try:
                        usage_payload = json.loads(usage_path.read_text(encoding="utf-8"))
                    except (json.JSONDecodeError, OSError) as exc:
                        st.error(f"Failed to read {usage_path.name}: {exc}")
                    else:
                        usage = usage_payload.get("usage") if isinstance(usage_payload, dict) else {}
                        summary = _extract_usage_numbers(usage)
                        if summary:
                            st.markdown("**Token usage:**")
                            labels = [
                                ("total_tokens", "Total"),
                                ("input_tokens", "Input"),
                                ("output_tokens", "Output"),
                                ("cached_input_tokens", "Cached input"),
                                ("reasoning_tokens", "Reasoning"),
                            ]
                            metrics = [(key, label) for key, label in labels if key in summary]
                            columns = st.columns(len(metrics))
                            for column, (key, label) in zip(columns, metrics):
                                column.metric(label, summary[key])
                show_markdown = st.checkbox(
                    "Render as markdown",
                    value=False,
                    help="Use the markdown exporter instead of the structured UI renderer.",
                )
                if show_markdown:
                    st.markdown(qa_json_to_markdown(qa_data))
                else:
                    _render_qa_json_structured(qa_data)

st.divider()
st.subheader("Markdown viewer")


def _read_markdown(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp1251")


available_markdowns = []
if QA_OUTPUT_DIR.exists():
    available_markdowns = sorted(
        QA_OUTPUT_DIR.glob("*.md"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

selected_markdowns = st.multiselect(
    "Select saved markdowns",
    available_markdowns,
    format_func=lambda path: path.name,
)
uploaded_markdowns = st.file_uploader(
    "Upload markdown files",
    type=["md"],
    accept_multiple_files=True,
)
markdown_path_input = st.text_input(
    "Or path to a markdown file/folder",
    value="",
)

if st.button("View selected markdowns"):
    rendered_any = False

    for markdown_path in selected_markdowns:
        try:
            content = _read_markdown(markdown_path)
        except OSError as exc:
            st.error(f"Failed to read {markdown_path.name}: {exc}")
        else:
            st.markdown(f"### {markdown_path.name}")
            st.markdown(content)
            rendered_any = True

    for markdown_file in uploaded_markdowns or []:
        content = markdown_file.getvalue().decode("utf-8", errors="ignore")
        st.markdown(f"### {markdown_file.name}")
        st.markdown(content)
        rendered_any = True

    if markdown_path_input:
        input_path = Path(markdown_path_input)
        if input_path.is_file() and input_path.suffix.lower() == ".md":
            try:
                content = _read_markdown(input_path)
            except OSError as exc:
                st.error(f"Failed to read {input_path.name}: {exc}")
            else:
                st.markdown(f"### {input_path.name}")
                st.markdown(content)
                rendered_any = True
        elif input_path.is_dir():
            markdown_paths = sorted(input_path.glob("*.md"))
            if not markdown_paths:
                st.warning("No .md files found in the folder.")
            for markdown_path in markdown_paths:
                try:
                    content = _read_markdown(markdown_path)
                except OSError as exc:
                    st.error(f"Failed to read {markdown_path.name}: {exc}")
                else:
                    st.markdown(f"### {markdown_path.name}")
                    st.markdown(content)
                    rendered_any = True
        else:
            st.warning("Path not found or not a markdown file.")

    if not rendered_any:
        st.info("No markdowns selected.")
