from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TextSpan(BaseModel):
    start_char: int | None = Field(
        default=None, ge=0, description="Start character index in the transcript text."
    )
    end_char: int | None = Field(
        default=None, ge=0, description="End character index in the transcript text."
    )



class AnswerError(BaseModel):
    category: Literal[
        "grammar",
        "vocabulary",
        "pronunciation",
        "fluency",
        "coherence",
        "structure",
        "register",
        "filler_words",
        "content",
        "other",
    ] = Field(description="Category of the error in the answer.")
    description: str = Field(description="What is wrong in the answer.")
    severity: Literal["low", "medium", "high"] | None = Field(
        default=None, description="Estimated severity of the error."
    )
    text_span: TextSpan | None = Field(
        default=None, description="Where the error appears in the transcript."
    )
    correction: str | None = Field(
        default=None, description="Suggested correction for the specific error."
    )
    rule_or_tip: str | None = Field(
        default=None, description="Optional rule or tip explaining the correction."
    )


class QAItem(BaseModel):
    question: str = Field(description="A concise formulation of the question asked by the interviewer, preserving important nuances.")
    approximate_timecode: str = Field(
        default=..., description="Approximate timecode when the question was asked."
    )
    place_in_the_text: str
    candidates_answer: str = Field(description="Essence of the Answer given by the candidate.")
    errors_and_problems: list[str] = Field(
        default_factory=list, description="List of errors in the candidate's answer."
    )
    what_to_fix: str 
    the_ideal_answer: str 
    text_span_QA: TextSpan = Field(
            default=..., description="Place of this Q/A in the transcript."
        )

class QAExtraction(BaseModel):
    vacancy: str | None = Field(
        default=None, description="Vacancy or position being interviewed for."
    )
    employee_role_identified: str 
    items: list[QAItem] = Field(
        default_factory=list,
        description="List of extracted interviewer question/candidate answer pairs.",
    )


prompt_QA_extractor = """
You are an expert at extracting question and answer pairs from interview transcripts.
Given a transcript of an interview. There are two people involved: the interviewer and the candidate for the vacancy: {vacancy}. 
Your task is to identify and extract the questions asked by the interviewer and the corresponding answers provided by the interviewee. 
Please follow these guidelines:
1. Identify each question asked by the interviewer.
2. Identify the corresponding answer provided by the interviewee.
3. If a question does not have a corresponding answer, it should be omitted from the output
4. Output the results in {language} language.
"""

prompt_chat_QA_extractor = """
Перед тобой файл с транскрибацией интервью. Учавствует 2 человека: Интервьюир и кандидат на вакансию {vacancy}. Подготовь Список вопрос - ответ из интервью в целом, примерное время на видео, когда он был задан, примерное место в тексте. список ошибок в ответе. и как нужно было правильно ответить.
"""