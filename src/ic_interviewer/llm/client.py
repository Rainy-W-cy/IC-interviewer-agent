"""Thin wrapper around the OpenAI Python SDK."""

from __future__ import annotations

from openai import OpenAI

from ic_interviewer.settings import Settings


class LLMClient:
    """Minimal text-generation client used by the first pipeline version."""

    def __init__(self, settings: Settings | None = None, client: OpenAI | None = None) -> None:
        self._settings = settings or Settings.from_env()
        api_key = self._settings.require_openai_api_key()
        self._model = self._settings.require_openai_model()
        self._client = client or OpenAI(api_key=api_key)

    def create_text(self, prompt: str, input_text: str) -> str:
        try:
            response = self._client.responses.create(
                model=self._model,
                instructions=prompt,
                input=input_text,
            )
        except Exception as exc:
            raise RuntimeError(f"OpenAI request failed: {exc}") from exc

        output_text = getattr(response, "output_text", None)
        if not output_text:
            raise RuntimeError("OpenAI response did not contain output_text.")

        return output_text
