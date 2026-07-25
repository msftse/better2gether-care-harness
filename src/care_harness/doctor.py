"""Pre-flight checks for demo day: `uv run care-harness --doctor`.

Verifies each leg of the architecture independently so a failure points straight
at the responsible party:

  1. Foundry auth      — can we mint an Entra token for the Foundry data plane?
  2. Foundry model     — does a 1-token chat call against the deployment succeed?
                         (fails with 403 until the data-plane role is assigned)
  3. Databricks auth   — does the service-principal OAuth token mint?
  4. Databricks agent  — does the Care Copilot endpoint answer?
                         (fails with 403 until the workspace IP ACL allows us)
"""

from __future__ import annotations

import httpx
from azure.identity import AzureCliCredential
from rich.console import Console
from rich.table import Table

from .config import Settings

console = Console()


async def run_doctor(settings: Settings) -> bool:
    results: list[tuple[str, bool, str]] = []

    # 1 + 2 — Azure AI Foundry
    token = None
    try:
        cred_kwargs: dict = {}
        if settings.foundry_subscription:
            cred_kwargs["subscription"] = settings.foundry_subscription
        elif settings.foundry_tenant_id:
            cred_kwargs["tenant_id"] = settings.foundry_tenant_id
        token = AzureCliCredential(**cred_kwargs).get_token("https://ai.azure.com/.default").token
        results.append(("Foundry: Entra token (az cli)", True, "token minted"))
    except Exception as exc:  # noqa: BLE001
        results.append(("Foundry: Entra token (az cli)", False, str(exc)[:160]))

    if token:
        try:
            async with httpx.AsyncClient(timeout=60) as http:
                resp = await http.post(
                    f"{settings.foundry_project_endpoint}/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "model": settings.foundry_model_deployment,
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_completion_tokens": 16,
                    },
                )
            ok = resp.status_code == 200
            hint = "model responded" if ok else f"HTTP {resp.status_code} {resp.text[:120]}"
            if resp.status_code in (401, 403):
                hint += " — assign a data-plane role (see README: RBAC)"
            results.append((f"Foundry: model '{settings.foundry_model_deployment}'", ok, hint))
        except Exception as exc:  # noqa: BLE001
            results.append(("Foundry: model call", False, str(exc)[:160]))

    # 3 + 4 — Databricks Care Copilot
    db_token = None
    try:
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.post(
                f"{settings.databricks_host}/oidc/v1/token",
                auth=(settings.databricks_client_id, settings.databricks_client_secret),
                data={"grant_type": "client_credentials", "scope": "all-apis"},
            )
            resp.raise_for_status()
            db_token = resp.json()["access_token"]
        results.append(("Databricks: SP OAuth token", True, "token minted"))
    except Exception as exc:  # noqa: BLE001
        results.append(("Databricks: SP OAuth token", False, str(exc)[:160]))

    if db_token:
        try:
            async with httpx.AsyncClient(timeout=120) as http:
                resp = await http.post(
                    f"{settings.databricks_host}/serving-endpoints/"
                    f"{settings.databricks_endpoint}/invocations",
                    headers={"Authorization": f"Bearer {db_token}"},
                    json={"input": [{"role": "user", "content": "Reply with the word pong."}]},
                )
            ok = resp.status_code == 200
            hint = "agent responded" if ok else f"HTTP {resp.status_code} {resp.text[:140]}"
            if resp.status_code == 403 and "IP ACL" in resp.text:
                hint = "workspace IP ACL blocks this network — ask Databricks admin to allowlist it"
            results.append((f"Databricks: endpoint '{settings.databricks_endpoint}'", ok, hint))
        except Exception as exc:  # noqa: BLE001
            results.append(("Databricks: endpoint call", False, str(exc)[:160]))

    table = Table(title="care-harness pre-flight")
    table.add_column("check")
    table.add_column("status")
    table.add_column("detail", overflow="fold")
    all_ok = True
    for name, ok, detail in results:
        all_ok &= ok
        table.add_row(name, "[green]PASS[/green]" if ok else "[red]FAIL[/red]", detail)
    console.print(table)
    return all_ok
