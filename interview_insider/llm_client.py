from __future__ import annotations

from typing import Literal, Type, TypeVar, Any

from openai import OpenAI
from pydantic import BaseModel

from interview_insider.prompts.extracton_models_and_prompts import QAExtraction

ModelChoice = Literal["5.2", "4.1", "o4-mini", "o3"]
T = TypeVar("T", bound=BaseModel)

_DEFAULT_MODEL_ALIASES: dict[str, str] = {
    "5.2": "gpt-5.2",
    "4.1": "gpt-4.1",
    "o4-mini": "o4-mini",
    "o3": "o3",
    "gpt-5.2": "gpt-5.2",
    "gpt-4.1": "gpt-4.1",
}


class LLMClient:
    def __init__(
        self,
        *,
        client: OpenAI | None = None,
        model_aliases: dict[str, str] | None = None,
    ) -> None:
        self._client = client or OpenAI()
        self._model_aliases = model_aliases or _DEFAULT_MODEL_ALIASES

    def resolve_model(self, model: str) -> str:
        resolved = self._model_aliases.get(model)
        if not resolved:
            supported = ", ".join(sorted({*("5.2", "4.1", "o4-mini", "o3")}))
            raise ValueError(f"Unsupported model '{model}'. Supported: {supported}")
        return resolved

    def _usage_to_dict(self, usage: Any | None) -> dict[str, Any]:
        if usage is None:
            return {}
        if isinstance(usage, dict):
            return usage
        if hasattr(usage, "model_dump"):
            return usage.model_dump()
        if hasattr(usage, "dict"):
            return usage.dict()
        if hasattr(usage, "__dict__"):
            return {key: value for key, value in usage.__dict__.items() if not key.startswith("_")}
        return {}

    def call_structured_llm(
        self,
        *,
        system_prompt: str,
        user_message: str,
        model: ModelChoice | str,
        response_model: Type[T],
    ) -> tuple[T, dict[str, Any]]:
        response = self._client.responses.parse(
            model=self.resolve_model(model),
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            text_format=response_model,
        )
        if response.output_parsed is None:
            raise ValueError("Model did not return structured output.")
        return response.output_parsed, self._usage_to_dict(response.usage)

    def extract_qa_json(
        self,
        *,
        system_prompt: str,
        user_message: str,
        model: ModelChoice | str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        extracted, usage = self.call_structured_llm(
            system_prompt=system_prompt,
            user_message=user_message,
            model=model,
            response_model=QAExtraction,
        )
        return extracted.model_dump(), usage
