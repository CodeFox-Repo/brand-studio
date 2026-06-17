from __future__ import annotations

from pathlib import Path

import pytest

from harness.config import ProviderConfig
from harness.providers import (
    GatewayImageProvider,
    GenerationRequest,
    GenerationResult,
    ImageProvider,
    OpenAIImageProvider,
    UnsupportedProviderError,
    available_provider_gateways,
    create_provider,
    register_provider,
)
from harness.providers.gateway import sanitize_metadata
from harness.providers.openai import build_openai_payload, choose_openai_size


class DummyProvider(ImageProvider):
    def generate(self, request: GenerationRequest, output_path: Path) -> GenerationResult:
        output_path.write_text("dummy", encoding="utf-8")
        return GenerationResult(
            asset_id=request.asset_id,
            path=output_path,
            seed=request.seed,
            mime_type="text/plain",
        )


def test_create_provider_uses_registered_generic_gateway() -> None:
    provider = create_provider(ProviderConfig(gateway="generic", model="flux-2-pro"))

    assert isinstance(provider, GatewayImageProvider)


def test_create_provider_uses_registered_openai_gateway() -> None:
    provider = create_provider(ProviderConfig(gateway="openai", model="gpt-image-1.5"))

    assert isinstance(provider, OpenAIImageProvider)


def test_create_provider_rejects_unknown_gateway() -> None:
    with pytest.raises(UnsupportedProviderError, match="not registered"):
        create_provider(ProviderConfig(gateway="missing-provider", model="flux-2-pro"))


def test_register_provider_adds_new_gateway() -> None:
    register_provider("dummy", lambda _config: DummyProvider())

    provider = create_provider(ProviderConfig(gateway="dummy", model="test-model"))

    assert isinstance(provider, DummyProvider)
    assert "dummy" in available_provider_gateways()


def test_choose_openai_size_matches_deliverable_orientation() -> None:
    assert choose_openai_size((1920, 600)) == "1536x1024"
    assert choose_openai_size((1080, 1920)) == "1024x1536"
    assert choose_openai_size((1080, 1080)) == "1024x1024"
    assert choose_openai_size((900, 383), "auto") == "auto"


def test_build_openai_payload_maps_harness_request() -> None:
    payload = build_openai_payload(
        GenerationRequest(
            asset_id="web-banner",
            prompt="Brand style\nSubject",
            negative_prompt="watermark",
            size=(1920, 600),
            seed=12345,
            gateway="openai",
            model="gpt-image-1.5",
            params={
                "quality": "medium",
                "output_format": "png",
                "retry_attempts": 3,
                "timeout_seconds": 120,
            },
        )
    )

    assert payload["model"] == "gpt-image-1.5"
    assert payload["size"] == "1536x1024"
    assert payload["quality"] == "medium"
    assert payload["output_format"] == "png"
    assert "Avoid: watermark" in payload["prompt"]


def test_sanitize_metadata_redacts_image_payloads() -> None:
    sanitized = sanitize_metadata(
        {
            "data": [
                {
                    "b64_json": "a" * 5000,
                    "revised_prompt": "ok",
                }
            ],
            "api_key": "secret",
        }
    )

    assert sanitized["data"][0]["b64_json"] == "[redacted image payload]"
    assert sanitized["data"][0]["revised_prompt"] == "ok"
    assert sanitized["api_key"] == "[redacted]"
