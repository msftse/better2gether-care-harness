"""Databricks Agent Bricks "Care Copilot" client, exposed as an Agent Framework tool.

The Care Copilot is a Multi-Agent Supervisor deployed as a Databricks Model Serving
endpoint that speaks the OpenAI Responses API. Internally it routes between:

  * a Genie space          — quantitative questions over the IoT wellness telemetry
  * a Knowledge Assistant  — SOPs, alert-code glossary, warranty/RMA policy docs
  * a web search tool      — published external guidance

Auth is OAuth machine-to-machine (client credentials). Bearer tokens live ~1 hour;
this client mints and caches them, refreshing 5 minutes before expiry, so the
harness can run indefinitely without a stale-token failure mid-demo.
"""

from __future__ import annotations

import asyncio
import re
import time
from typing import Annotated, Any

import httpx
from pydantic import Field

from .config import Settings

_TOKEN_REFRESH_MARGIN_S = 300
_ROUTING_MARKER = re.compile(r"<name>([^<]+)</name>")


class CareCopilotError(RuntimeError):
    """Raised when the Care Copilot endpoint cannot be reached or errors out."""


class CareCopilotClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._token: str | None = None
        self._token_expiry: float = 0.0
        self._lock = asyncio.Lock()
        self._http = httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=15.0))

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _get_token(self) -> str:
        async with self._lock:
            if self._token and time.monotonic() < self._token_expiry:
                return self._token
            resp = await self._http.post(
                f"{self._settings.databricks_host}/oidc/v1/token",
                auth=(self._settings.databricks_client_id, self._settings.databricks_client_secret),
                data={"grant_type": "client_credentials", "scope": "all-apis"},
            )
            resp.raise_for_status()
            payload = resp.json()
            self._token = payload["access_token"]
            expires_in = int(payload.get("expires_in", 3600))
            self._token_expiry = time.monotonic() + expires_in - _TOKEN_REFRESH_MARGIN_S
            return self._token

    async def ask(self, question: str) -> str:
        """Send one question to the supervisor and return the final answer text."""
        token = await self._get_token()
        resp = await self._http.post(
            f"{self._settings.databricks_host}/serving-endpoints/"
            f"{self._settings.databricks_endpoint}/invocations",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"input": [{"role": "user", "content": question}]},
        )
        if resp.status_code == 403 and "IP ACL" in resp.text:
            raise CareCopilotError(
                "The Databricks workspace IP access list blocked this call. "
                "Ask the Databricks admin to allowlist this network's egress IP. "
                f"Details: {resp.text}"
            )
        if resp.status_code >= 400:
            raise CareCopilotError(
                f"Care Copilot endpoint returned HTTP {resp.status_code}: {resp.text[:500]}"
            )
        return _extract_answer(resp.json())


def _extract_answer(payload: dict[str, Any]) -> str:
    """Pull the final assistant text and the internal routing out of a Responses payload.

    The supervisor emits interleaved text chunks separated by `<name>agent</name>`
    markers showing which sub-agent produced each chunk. The last substantive chunk
    is the supervisor's final synthesized answer; the markers tell us which
    sub-agents (Genie, Knowledge Assistant, web) were consulted.
    """
    routed_to: list[str] = []
    final = ""
    for item in payload.get("output", []):
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for chunk in content:
            text = chunk.get("text", "")
            if not text:
                continue
            for name in _ROUTING_MARKER.findall(text):
                if name not in routed_to:
                    routed_to.append(name)
            # Strip inline routing markers; the last chunk with substantive
            # text is the supervisor's final synthesized answer.
            substantive = _ROUTING_MARKER.sub("", text).strip()
            if substantive:
                final = substantive

    if not final:
        return "(the Care Copilot returned no text — inspect the raw payload)"

    if routed_to:
        final += "\n\n[care-copilot routing: consulted " + ", ".join(routed_to) + "]"
    return final


def make_care_copilot_tool(client: CareCopilotClient):
    """Build the tool function handed to the harness agent."""

    async def ask_care_copilot(
        question: Annotated[
            str,
            Field(
                description=(
                    "A complete, self-contained natural-language question for the "
                    "Better2gether Care Copilot. Include member/device ids (e.g. "
                    "watch-007) and any relevant context from the conversation."
                )
            ),
        ],
    ) -> str:
        """Ask the Better2gether Care Copilot (Databricks Agent Bricks supervisor).

        Use this for quantitative questions about the Better2gether wellness
        program's live data: member telemetry and alert events (SpO2, battery,
        heart rate, temperature), alert counts and breakdowns by region/plan/
        firmware, and per-device stats — answered by a Genie space over the
        vitals_alerts and device_registry tables. Prefer one rich question over
        many small ones.
        """
        try:
            return await client.ask(question)
        except CareCopilotError as exc:
            return f"ERROR from Care Copilot: {exc}"

    return ask_care_copilot
