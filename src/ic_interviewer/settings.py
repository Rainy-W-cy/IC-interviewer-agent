"""Environment-backed settings for external integrations."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None = None
    openai_model: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL"),
        )

    def require_openai_api_key(self) -> str:
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set.")
        return self.openai_api_key

    def require_openai_model(self) -> str:
        if not self.openai_model:
            raise ValueError("OPENAI_MODEL is not set.")
        return self.openai_model
