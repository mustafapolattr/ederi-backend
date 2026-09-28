"""Provider isolation tests — no real network call is ever made; requests
is mocked in every test (per project rule: tests never call the real LLM)."""

from unittest.mock import Mock, patch

import pytest
import requests

from apps.ai import llm


@pytest.fixture(autouse=True)
def api_key(settings):
    settings.LLM_API_KEY = "test-key"
    settings.LLM_MODEL = "gemini-flash-lite-latest"


def _response(status_code=200, json_body=None):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = json_body or {}
    return response


class TestGenerate:
    @patch("apps.ai.llm.requests.post")
    def test_returns_text_from_first_candidate(self, mock_post):
        mock_post.return_value = _response(
            200, {"candidates": [{"content": {"parts": [{"text": "Hello there"}]}}]}
        )

        result = llm.generate("prompt")

        assert result == "Hello there"
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["params"] == {"key": "test-key"}
        assert call_kwargs["json"]["contents"][0]["parts"][0]["text"] == "prompt"

    @patch("apps.ai.llm.requests.post")
    def test_rate_limited_raises_specific_error(self, mock_post):
        mock_post.return_value = _response(429)

        with pytest.raises(llm.LLMRateLimitedError):
            llm.generate("prompt")

    @patch("apps.ai.llm.requests.post")
    def test_non_200_raises_llm_error(self, mock_post):
        mock_post.return_value = _response(500)

        with pytest.raises(llm.LLMError):
            llm.generate("prompt")

    @patch("apps.ai.llm.requests.post")
    def test_network_failure_raises_llm_error(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("boom")

        with pytest.raises(llm.LLMError):
            llm.generate("prompt")

    @patch("apps.ai.llm.requests.post")
    def test_malformed_response_shape_raises_llm_error(self, mock_post):
        mock_post.return_value = _response(200, {"unexpected": "shape"})

        with pytest.raises(llm.LLMError):
            llm.generate("prompt")

    def test_missing_api_key_raises_without_network_call(self, settings):
        settings.LLM_API_KEY = ""
        with pytest.raises(llm.LLMError):
            llm.generate("prompt")
