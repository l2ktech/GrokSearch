import httpx
import pytest

from grok_search.config import config
from grok_search.providers.grok import GrokSearchProvider


def _http_status_error(status_code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "http://example.com/v1/chat/completions")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError(
        f"status={status_code}",
        request=request,
        response=response,
    )


def test_config_maps_grok_420_to_grok_41_fallbacks(monkeypatch):
    monkeypatch.delenv("GROK_ENABLE_MODEL_FALLBACK", raising=False)
    monkeypatch.delenv("GROK_FALLBACK_MODELS", raising=False)

    assert config.get_fallback_models_for("grok-4.20-beta") == (
        "grok-4.1-fast",
        "grok-4.1-thinking",
        "grok-4",
    )
    assert config.get_fallback_models_for("grok-4.1-fast") == ()


@pytest.mark.asyncio
async def test_provider_falls_back_when_grok_420_returns_502(monkeypatch):
    provider = GrokSearchProvider("http://example.com/v1", "dummy", "grok-4.20-beta")
    attempted_models = []

    async def fake_execute(headers, payload, ctx=None):
        attempted_models.append(payload["model"])
        if payload["model"] == "grok-4.20-beta":
            raise _http_status_error(502)
        return "fallback-ok"

    async def fake_log_info(ctx, message, debug_enabled):
        return None

    monkeypatch.setattr(config, "get_fallback_models_for", lambda model: ("grok-4.1-fast",))
    monkeypatch.setattr("grok_search.providers.grok.log_info", fake_log_info)
    monkeypatch.setattr(provider, "_execute_payload_with_retry", fake_execute)

    result = await provider._execute_stream_with_retry(
        headers={"Authorization": "Bearer test"},
        payload={"model": "grok-4.20-beta", "messages": [], "stream": False},
    )

    assert result == "fallback-ok"
    assert attempted_models == ["grok-4.20-beta", "grok-4.1-fast"]
