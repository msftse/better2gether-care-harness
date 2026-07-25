# Connect the Care Copilot Supervisor to Azure AI Foundry

Because you build and host the Supervisor in **your own Databricks workspace**, its serving
endpoint is reachable from your Azure tenant with no cross-org IP restrictions. The endpoint
speaks the **OpenAI-compatible Responses API**, so Foundry connects as a custom /
OpenAI-compatible model connection.

## What you need

| Item | Where to find it |
|---|---|
| **Workspace host** | your workspace URL, e.g. `https://adb-xxxx.azuredatabricks.net` |
| **Endpoint name** | Serving page — the Supervisor endpoint, e.g. `mas-xxxxxxxx-endpoint` |
| **Auth token** | an OAuth token (see below). For a standing connection use a **service principal**. |

## Base URL & model for Foundry

| Foundry field | Value |
|---|---|
| Base URL / target | `https://<your-host>/serving-endpoints` |
| Model / deployment name | `<your-mas-endpoint-name>` |
| API key | a bearer token (see auth) |
| API flavor | OpenAI-compatible — **Responses** API |

## Auth — use a service principal (recommended for Foundry)

A personal token expires in ≤90 days and is tied to you. For a standing Foundry connection,
create a service principal scoped to just this agent:

```bash
# 1) create the SP
databricks service-principals create --profile care --json '{
  "displayName": "foundry-care-copilot",
  "entitlements": [{"value": "workspace-access"}]
}'
# note the "applicationId" (client_id) and numeric "id"

# 2) create an OAuth secret (client secret)
databricks service-principal-secrets-proxy create <SP_NUMERIC_ID> --profile care -o json
# note "secret" (client_secret)

# 3) grant it least privilege (IMPORTANT: the Supervisor runs tools AS the caller,
#    so the SP needs the endpoint AND everything the tools touch)
#    - CAN_QUERY on the Supervisor endpoint
#    - CAN_QUERY on the Knowledge Assistant endpoint
#    - CAN_RUN on the Genie space
#    - USE_CATALOG on the catalog, USE_SCHEMA + SELECT on the schema
#    - CAN_USE on the SQL warehouse
```
(Do these grants in the UI, or mirror the commands in `test/grant_sp.sh`.)

### Minting a token from the SP (Foundry needs a fresh one; it expires ~1h)

```
POST https://<your-host>/oidc/v1/token
  auth = (client_id, client_secret)         # HTTP basic
  body = grant_type=client_credentials&scope=all-apis
  -> { "access_token": "...", "expires_in": 3600 }
```

The **client_id + client_secret don't expire quickly** — only the derived token does. Have
your Foundry side (or a small wrapper) mint a fresh token before each session, or store the
client_id/secret in Azure Key Vault and refresh programmatically. Don't hard-code a one-off token.

## Two ways to wire it in Foundry

- **Option A — OpenAI-compatible model connection:** add the base URL + token as a custom /
  serverless OpenAI-compatible model. Use it in the playground and prompt flows.
- **Option B — tool/OpenAPI action on a Foundry agent (cleaner for orchestration):** register
  the endpoint as an external action so a Foundry agent calls the Supervisor as one specialist.

## Note on response shape

The Supervisor returns a **Responses-style** payload (richer than plain chat.completions — it
includes the tool/agent routing). Use the Responses API path and test one call before relying
on it in a flow. See `test/test_api.py` for a working call.
