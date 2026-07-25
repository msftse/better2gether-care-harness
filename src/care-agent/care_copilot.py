"""Databricks Agent Bricks "Care Copilot" client for the hosted agent.

Self-contained copy for the Foundry-hosted deployment (the service directory is
uploaded as-is). Mirrors src/care_harness/care_copilot.py: OAuth M2M token
caching with early refresh, Responses-payload parsing with sub-agent routing
markers, and a tool factory.
"""

from __future__ import annotations

import asyncio
import os
import re
import time
from typing import Annotated, Any

import httpx
from pydantic import Field

_TOKEN_REFRESH_MARGIN_S = 300
_ROUTING_MARKER = re.compile(r"<name>([^<]+)</name>")


class CareCopilotError(RuntimeError):
    """Raised when the Care Copilot endpoint cannot be reached or errors out."""


class CareCopilotClient:
    """Reads DATABRICKS_* configuration from the environment."""

    def __init__(self) -> None:
        self._host = os.environ["DATABRICKS_HOST"].rstrip("/")
        self._endpoint = os.environ["DATABRICKS_SERVING_ENDPOINT"]
        self._client_id = os.environ["DATABRICKS_CLIENT_ID"]
        self._client_secret = os.environ["DATABRICKS_CLIENT_SECRET"]
        self._token: str | None = None
        self._token_expiry: float = 0.0
        self._lock = asyncio.Lock()
        self._http = httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=15.0))

    async def _get_token(self) -> str:
        async with self._lock:
            if self._token and time.monotonic() < self._token_expiry:
                return self._token
            resp = await self._http.post(
                f"{self._host}/oidc/v1/token",
                auth=(self._client_id, self._client_secret),
                data={"grant_type": "client_credentials", "scope": "all-apis"},
            )
            resp.raise_for_status()
            payload = resp.json()
            self._token = payload["access_token"]
            expires_in = int(payload.get("expires_in", 3600))
            self._token_expiry = time.monotonic() + expires_in - _TOKEN_REFRESH_MARGIN_S
            return self._token

    async def ask(self, question: str) -> str:
        token = await self._get_token()
        resp = await self._http.post(
            f"{self._host}/serving-endpoints/{self._endpoint}/invocations",
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
            substantive = _ROUTING_MARKER.sub("", text).strip()
            if substantive:
                final = substantive

    if not final:
        return "(the Care Copilot returned no text — inspect the raw payload)"
    if routed_to:
        final += "\n\n[care-copilot routing: consulted " + ", ".join(routed_to) + "]"
    return final


def make_care_copilot_tool(client: CareCopilotClient):
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

        Use this for ANYTHING about the Better2gether wellness program: member
        telemetry and alert data (SpO2, battery, disconnects — answered by a Genie
        space over the IoT data), care SOPs / alert-code meanings / warranty & RMA
        policy (answered by a Knowledge Assistant over the program docs), and
        published external health guidance (answered by its web tool). Prefer one
        rich question over many small ones.
        """
        try:
            return await client.ask(question)
        except CareCopilotError as exc:
            return f"ERROR from Care Copilot: {exc}"

    return ask_care_copilot
