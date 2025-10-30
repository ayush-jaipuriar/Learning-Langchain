"""LLM provider factory for the Vertex-backed SuperBot agent."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Mapping, Optional

from langchain_google_vertexai import ChatVertexAI

logger = logging.getLogger(__name__)


class SuperBotConfigError(RuntimeError):
    """Raised when required Vertex AI configuration is missing or invalid."""


class SuperBotProviderError(RuntimeError):
    """Raised when the Vertex AI chat model cannot be instantiated."""


@dataclass
class VertexConfig:
    """Configuration for initializing the Vertex AI chat model."""

    project_id: str
    location: str
    model_name: str
    temperature: float = 0.2
    max_output_tokens: int = 1024

    @classmethod
    def from_env(
        cls,
        environ: Optional[Mapping[str, str]] = None,
    ) -> "VertexConfig":
        """Construct a config object from environment variables.

        Parameters
        ----------
        environ:
            Optional mapping used for dependency injection/testing. Defaults to
            ``os.environ``.
        """

        env = environ or os.environ

        project_id = env.get("GCP_PROJECT_ID")
        if not project_id:
            raise SuperBotConfigError(
                "Missing GCP_PROJECT_ID. Set it in the environment or the SuperBot env template."
            )

        location = env.get("GCP_LOCATION")
        if not location:
            raise SuperBotConfigError(
                "Missing GCP_LOCATION. Provide the Vertex AI region, e.g., 'us-central1'."
            )

        model_name = env.get("VERTEX_MODEL", "gemini-1.5-flash-001")

        temperature_raw = env.get("VERTEX_TEMPERATURE", "0.2")
        max_tokens_raw = env.get("VERTEX_MAX_OUTPUT_TOKENS", "1024")

        try:
            temperature = float(temperature_raw)
        except (TypeError, ValueError) as exc:
            raise SuperBotConfigError(
                f"VERTEX_TEMPERATURE must be a float-compatible value, got {temperature_raw!r}."
            ) from exc

        try:
            max_output_tokens = int(max_tokens_raw)
        except (TypeError, ValueError) as exc:
            raise SuperBotConfigError(
                f"VERTEX_MAX_OUTPUT_TOKENS must be an integer-compatible value, got {max_tokens_raw!r}."
            ) from exc

        return cls(
            project_id=project_id,
            location=location,
            model_name=model_name,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )


def build_vertex_chat_model(config: Optional[VertexConfig] = None) -> ChatVertexAI:
    """Instantiate a Vertex AI chat model using the provided or environment config."""

    cfg = config or VertexConfig.from_env()

    logger.info(
        "Initializing Vertex AI chat model",
        extra={
            "vertex_project": cfg.project_id,
            "vertex_location": cfg.location,
            "vertex_model": cfg.model_name,
            "vertex_temperature": cfg.temperature,
            "vertex_max_output_tokens": cfg.max_output_tokens,
        },
    )

    try:
        return ChatVertexAI(
            project=cfg.project_id,
            location=cfg.location,
            model_name=cfg.model_name,
            temperature=cfg.temperature,
            max_output_tokens=cfg.max_output_tokens,
        )
    except Exception as exc:  # pragma: no cover - surface provider errors
        logger.exception("Failed to initialize Vertex AI chat model: %s", exc)
        raise SuperBotProviderError(
            "Vertex AI chat model initialization failed. "
            "Check project permissions, model availability, and ADC setup."
        ) from exc


__all__ = [
    "SuperBotConfigError",
    "SuperBotProviderError",
    "VertexConfig",
    "build_vertex_chat_model",
]

