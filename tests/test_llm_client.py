from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from ic_interviewer.llm.client import LLMClient
from ic_interviewer.settings import Settings


def test_settings_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")

    settings = Settings.from_env()

    assert settings.openai_api_key == "test-key"
    assert settings.openai_model == "gpt-test"


def test_client_create_text_returns_output() -> None:
    mock_client = Mock()
    mock_client.responses.create.return_value = SimpleNamespace(output_text="generated text")

    client = LLMClient(
        settings=Settings(openai_api_key="test-key", openai_model="gpt-test"),
        client=mock_client,
    )

    result = client.create_text(prompt="be concise", input_text="resume content")

    assert result == "generated text"
    mock_client.responses.create.assert_called_once_with(
        model="gpt-test",
        instructions="be concise",
        input="resume content",
    )


def test_client_raises_clear_error_when_request_fails() -> None:
    mock_client = Mock()
    mock_client.responses.create.side_effect = Exception("network unavailable")

    client = LLMClient(
        settings=Settings(openai_api_key="test-key", openai_model="gpt-test"),
        client=mock_client,
    )

    with pytest.raises(RuntimeError, match="OpenAI request failed: network unavailable"):
        client.create_text(prompt="prompt", input_text="text")


def test_client_raises_clear_error_for_missing_output_text() -> None:
    mock_client = Mock()
    mock_client.responses.create.return_value = SimpleNamespace(output_text="")

    client = LLMClient(
        settings=Settings(openai_api_key="test-key", openai_model="gpt-test"),
        client=mock_client,
    )

    with pytest.raises(RuntimeError, match="did not contain output_text"):
        client.create_text(prompt="prompt", input_text="text")


def test_client_initializes_openai_sdk_from_settings() -> None:
    with patch("ic_interviewer.llm.client.OpenAI") as mock_openai:
        mock_sdk_client = Mock()
        mock_openai.return_value = mock_sdk_client

        client = LLMClient(
            settings=Settings(openai_api_key="test-key", openai_model="gpt-test"),
        )

    assert client._client is mock_sdk_client
    mock_openai.assert_called_once_with(api_key="test-key")


def test_client_requires_env_values() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
        LLMClient(settings=Settings(openai_api_key=None, openai_model="gpt-test"), client=Mock())

    with pytest.raises(ValueError, match="OPENAI_MODEL is not set"):
        LLMClient(settings=Settings(openai_api_key="test-key", openai_model=None), client=Mock())
