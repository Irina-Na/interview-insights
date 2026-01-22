from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class QAItem(BaseModel):
    question: str = Field(description="A concise formulation of the question asked by the interviewer, preserving important nuances")
    timecode: str = Field(
        default=..., description="Timecode when the question was asked"
    )
    place_in_the_text: str = Field(description="semantic block reference point in the transcript text") 
    candidates_answer: str = Field(description="Essence of the Answer given by the candidate")
    short_candidate_answer_evaluation: str 
    errors_and_problems: list[str] = Field(
        default_factory=list, description="List of errors in the candidate's answer"
    )
    what_to_fix: str 
    the_ideal_answer_example_eng: str 
    the_ideal_answer_example_ru: str 
    key_idea: str

class QAExtraction(BaseModel):
    vacancy: str | None = Field(
        default=None, description="Vacancy or position being interviewed for"
    )
    employee_role_identified: str 
    stages_of_conversation_short: list[str]
    items: list[QAItem] = Field(
        default_factory=list,
        description="List of extracted interviewer question/candidate answer pairs",
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
