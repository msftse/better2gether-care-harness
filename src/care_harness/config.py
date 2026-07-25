"""Environment-driven configuration for the care harness POC.

All secrets live in `.env` (never committed). See `.env.example` for the template.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file) or CWD.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv()  # also honor a .env in the current working directory


@dataclass(frozen=True)
class Settings:
    # Azure AI Foundry — powers the harness agent itself
    foundry_project_endpoint: str
    foundry_model_deployment: str
    foundry_tenant_id: str | None
    foundry_subscription: str | None

    # Databricks — the Agent Bricks "Care Copilot" multi-agent supervisor endpoint
    databricks_host: str
    databricks_endpoint: str
    databricks_client_id: str
    databricks_client_secret: str

    # Harness behavior
    disable_web_search: bool
    max_context_window_tokens: int
    max_output_tokens: int


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(
            f"Missing required environment variable {name}. "
            f"Copy .env.example to .env and fill it in."
        )
    return value


def load_settings() -> Settings:
    return Settings(
        foundry_project_endpoint=_require("FOUNDRY_PROJECT_ENDPOINT"),
        foundry_model_deployment=os.environ.get("FOUNDRY_MODEL_DEPLOYMENT", "gpt-5.4-mini"),
        foundry_tenant_id=os.environ.get("FOUNDRY_TENANT_ID") or None,
        foundry_subscription=os.environ.get("FOUNDRY_SUBSCRIPTION_ID") or None,
        databricks_host=_require("DATABRICKS_HOST").rstrip("/"),
        databricks_endpoint=_require("DATABRICKS_SERVING_ENDPOINT"),
        databricks_client_id=_require("DATABRICKS_CLIENT_ID"),
        databricks_client_secret=_require("DATABRICKS_CLIENT_SECRET"),
        # Hosted web search needs a Bing-grounding-enabled Foundry project; the
        # Databricks supervisor has its own web tool, so this is opt-in.
        disable_web_search=os.environ.get("HARNESS_ENABLE_WEB_SEARCH", "").lower()
        not in ("1", "true", "yes"),
        max_context_window_tokens=int(os.environ.get("HARNESS_MAX_CONTEXT_TOKENS", "272000")),
        max_output_tokens=int(os.environ.get("HARNESS_MAX_OUTPUT_TOKENS", "16384")),
    )
