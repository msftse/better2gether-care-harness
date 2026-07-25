# Better2gether Care Copilot — Build-in-Your-Workspace Kit

This kit lets you (or your coding agent) build the **Care Copilot** multi-agent system in
**your own Databricks workspace** and connect it to **Azure AI Foundry** for the demo. Because
everything runs in your workspace/tenant, there are no cross-org IP restrictions — your Foundry
calls hit your own serving endpoint directly.

## What you're building

A **Multi-Agent Supervisor** ("Care Copilot") for a wellness wearables company, orchestrating:
- **Genie** — quantitative answers over vitals alerts + device fleet data
- **Knowledge Assistant** — qualitative answers over care/support documentation
- **Web Search** (optional) — public health/device references

…then exposed as a REST serving endpoint and wired into **Azure AI Foundry**.

## Prerequisites in your workspace

- A **Serverless** Databricks workspace with **Unity Catalog**, **Genie**, **Vector Search**,
  and **Agent Bricks** enabled (Agent Bricks needs serverless).
- A serverless **SQL warehouse** (note its warehouse id).
- Databricks CLI installed and authenticated:
  `databricks auth login --host https://<your-host> --profile care`

## Steps (in order)

| # | Step | File | ~time |
|---|------|------|-------|
| 1 | Create tables + volume | `sql/01_setup_data.sql` (run in SQL editor) | 2 min |
| 2 | Upload the 8 KB docs to the volume | `kb_docs/` → Catalog Explorer upload, or `sql/02_upload_kb_docs.py` | 2 min |
| 3 | Create the Genie space | `genie/create_genie_space.py` (or build in UI) | 3 min |
| 4 | Build Knowledge Assistant + Supervisor | `agent_bricks/BUILD_AGENTS.md` (UI) | 15 min |
| 5 | (For API access) create a scoped service principal | `test/grant_sp.sh` | 3 min |
| 6 | Test the REST endpoint | `test/test_api.py` | 2 min |
| 7 | Connect to Azure AI Foundry | `foundry/CONNECT_FOUNDRY.md` | 10 min |

## Contents

```
README.md                     ← you are here
sql/
  01_setup_data.sql           ← device_registry + vitals_alerts + care_kb volume
  02_upload_kb_docs.py        ← optional notebook to push docs into the volume
kb_docs/                      ← 8 knowledge-base markdown files (KA source)
genie/
  create_genie_space.py       ← creates the Genie space via REST
agent_bricks/
  BUILD_AGENTS.md             ← UI steps for KA + Supervisor (+ all paste-text)
test/
  test_api.py                 ← call the Supervisor over REST (what Foundry does)
  grant_sp.sh                 ← least-privilege grants for a service principal
foundry/
  CONNECT_FOUNDRY.md          ← wire the endpoint into Azure AI Foundry
```

## Notes / gotchas

- **Agent Bricks is UI-only** — the KA and Supervisor can't be created by API/DAB, so step 4 is
  manual clicks. Everything else is scripted.
- **KA index sync** — after creating the Knowledge Assistant, its document index takes a few
  minutes to sync. Don't test the Supervisor's doc questions until the KA answers on its own.
- **The Supervisor runs tools as the caller** — so a service principal calling it needs access
  not just to the Supervisor endpoint but to the KA endpoint, Genie space, and underlying
  tables/warehouse (see `test/grant_sp.sh`).
- **Catalog/schema** default to `better2gether.care_copilot` — change consistently across all files if
  you use a different one.
- **Data is synthetic**; `watch-007` is seeded for the demo money-shot (9 SPO2-CRIT / 13 SPO2-LOW),
  and `watch-001..005` are on legacy firmware `v2.3.8` for the firmware-campaign story.
