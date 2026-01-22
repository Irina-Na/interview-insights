from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = [str(item).strip() for item in value]
        return [item for item in items if item]
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    text = str(value).strip()
    return [text] if text else []


def qa_json_to_markdown(qa_json: dict[str, Any]) -> str:
    lines: list[str] = []

    vacancy = str(qa_json.get("vacancy") or "").strip()
    if vacancy:
        lines.append(f"# Interview Insights - {vacancy}")
    else:
        lines.append("# Interview Insights")

    role = str(qa_json.get("employee_role_identified") or "").strip()
    if role:
        lines.append(f"**????:** {role}")
        lines.append("")

    stages = _normalize_list(qa_json.get("stages_of_conversation_short"))
    if stages:
        lines.append("**?????? ?????????:**")
        lines.extend(f"- {stage}" for stage in stages)
        lines.append("")

    items = qa_json.get("items") or []
    if not isinstance(items, list):
        items = []

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue

        question = str(item.get("question") or "").strip()
        title = f"## Q{index}. {question}" if question else f"## Q{index}"
        lines.append(title)

        timecode = str(item.get("timecode") or "").strip()
        place = str(item.get("place_in_the_text") or "").strip()
        if timecode:
            lines.append(f"- **?????:** {timecode}")
        if place:
            lines.append(f"- **????? ? ??????:** {place}")

        candidate_answer = str(item.get("candidates_answer") or "").strip()
        if candidate_answer:
            lines.append("")
            lines.append("**????? ????????? (??????):**")
            lines.append(candidate_answer)

        short_eval = str(item.get("short_candidate_answer_evaluation") or "").strip()
        if short_eval:
            lines.append("")
            lines.append("**??????? ?????? ??????:**")
            lines.append(short_eval)

        key_idea = str(item.get("key_idea") or "").strip()
        if key_idea:
            lines.append("")
            lines.append("**Ключевая идея:**")
            lines.append(key_idea)

        errors = _normalize_list(item.get("errors_and_problems"))
        if errors:
            lines.append("")
            lines.append("**??????:**")
            lines.extend(f"- {error}" for error in errors)

        improvements = _normalize_list(item.get("what_to_fix"))
        if improvements:
            lines.append("")
            lines.append("**??? ???????? ?????:**")
            lines.extend(f"- {tip}" for tip in improvements)

        ideal_ru = str(item.get("the_ideal_answer_example_ru") or "").strip()
        ideal_en = str(item.get("the_ideal_answer_example_eng") or "").strip()
        if ideal_ru or ideal_en:
            lines.append("")
            lines.append("**??????:**")
            if ideal_ru:
                lines.append("*RU:*")
                lines.append(f"> {ideal_ru}")
            if ideal_en:
                lines.append("*EN:*")
                lines.append(f"> {ideal_en}")

        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def save_markdown_for_qa_json(qa_json: dict[str, Any], json_path: Path) -> Path:
    markdown_text = qa_json_to_markdown(qa_json)
    output_path = json_path.with_suffix(".md")
    output_path.write_text(markdown_text, encoding="utf-8")
    return output_path


def save_markdown_for_qa_json_path(json_path: Path) -> Path:
    qa_json = json.loads(json_path.read_text(encoding="utf-8"))
    return save_markdown_for_qa_json(qa_json, json_path)
