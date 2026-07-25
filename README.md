<div align="center">

<img src="docs/banner.png" alt="Azure AI Foundry ♥ Azure Databricks" width="860" />

<h1>Better2gether Care Harness</h1>

<b>Microsoft Agent Framework harness × Azure AI Foundry × Databricks Genie</b><br/>
<i>The agent pattern that respects Unity Catalog — implemented end-to-end</i>

<br/>

<img src="https://img.shields.io/badge/Azure%20AI%20Foundry-hosted%20agent-0078D4?logo=microsoftazure&logoColor=white" />
<img src="https://img.shields.io/badge/Agent%20Framework-harness%201.12-5E5E5E" />
<img src="https://img.shields.io/badge/Databricks-Genie%20%2B%20Agent%20Bricks-FF3621?logo=databricks&logoColor=white" />
<img src="https://img.shields.io/badge/Unity%20Catalog-governed-1B3139" />

</div>

---



POC of the **[Microsoft Agent Framework harness](https://learn.microsoft.com/en-us/agent-framework/agents/harness)**
(`create_harness_agent`, released July 2026) running on **Azure AI Foundry**, with the
**Databricks Agent Bricks "Care Copilot"** — a Multi-Agent Supervisor that routes to a
**Genie space**, a **Knowledge Assistant**, and a **web tool** — wired in as a first-class tool.

```mermaid
flowchart LR
    U[Care agent / CLI] --> H

    subgraph Azure["Azure AI Foundry — b2g-care-foundry / care-poc"]
        H["Agent Framework HARNESS<br/>(gpt-5.4-mini)<br/>tool loop · todo/plan · modes ·<br/>file memory · compaction ·<br/>history persistence · OTel"]
    end

    H -- "ask_care_copilot(question)<br/>OAuth M2M bearer (auto-refresh)" --> S

    subgraph Databricks["Databricks — Agent Bricks"]
        S["Care Copilot<br/>Multi-Agent Supervisor<br/>mas-a8f5ce73-endpoint"]
        S --> G["Genie space<br/>IoT telemetry SQL"]
        S --> K["Knowledge Assistant<br/>SOPs · alert glossary · RMA"]
        S --> W["Web tool<br/>WHO / Mayo guidance"]
    end
```

Two agentic runtimes, cleanly separated:

* **The harness (Foundry)** owns the conversation: multi-turn session memory, planning
  (todo list + plan/execute modes), context compaction, per-call history persistence,
  tool approval, and OpenTelemetry — all on by default from `create_harness_agent`.
* **The Care Copilot (Databricks)** owns the data: it decides internally whether a
  question needs Genie (SQL over the wellness telemetry), the Knowledge Assistant
  (program docs), the web, or all three. The harness treats it as one tool and
  surfaces the routing in its answers (`[care-copilot routing: consulted …]`).

## The pattern — "the agent pattern that respects Unity Catalog"

This POC is a working implementation of the architecture described by Pablo Castaño in
**[Microsoft Foundry + Databricks Genie: the agent pattern that respects Unity Catalog](https://medium.com/@depablocastano/microsoft-foundry-databricks-genie-the-agent-pattern-that-respects-unity-catalog-a5a06852c5f9)**:
a Foundry agent owns the conversation, delegates analytical questions to a **Databricks Genie
Space**, and lets **Unity Catalog** — not the agent — decide who sees what. No shadow permission
model, no re-implemented access control: the agent asks, Genie translates to SQL over certified
tables, Unity Catalog enforces grants at query time.

<p align="center">
  <img src="https://miro.medium.com/v2/resize:fit:700/1*jMNvY7AHJrxKHci1XdE8Gw.png" width="680" alt="Foundry Agent delegates analytical questions to a Databricks Genie Space over Unity Catalog"/>
  <br/><sub>A Foundry Agent handles the conversation, then delegates analytical questions to a Databricks Genie Space over Unity Catalog. <i>Diagram © <a href="https://medium.com/@depablocastano">Pablo Castaño</a>, from the article.</i></sub>
</p>

<p align="center">
  <img src="https://miro.medium.com/v2/resize:fit:700/1*vHuG53ULNc9MUaDBxOAz1Q.png" width="680" alt="Runtime sequence: token exchange and Genie call, Unity Catalog enforces who can see what"/>
  <br/><sub>Runtime sequence — the caller's token is forwarded with the Genie call and Unity Catalog enforces who can see what. <i>Diagram © <a href="https://medium.com/@depablocastano">Pablo Castaño</a>, from the article.</i></sub>
</p>

<p align="center">
  <img src="https://miro.medium.com/v2/resize:fit:700/1*f_V8V6z379S3mMl4J9gVPg.png" width="680" alt="Two users hit the same Foundry Agent; Unity Catalog decides who sees what"/>
  <br/><sub>The VP and the regional rep hit the same agent; Unity Catalog decides who sees what. <i>Diagram © <a href="https://medium.com/@depablocastano">Pablo Castaño</a>, from the article.</i></sub>
</p>

### How this repo maps to the article

| Article component | This POC |
|---|---|
| Foundry Agent (conversation + routing) | Agent Framework **harness** (`create_harness_agent`, gpt-5.4-mini) — local CLI *and* Foundry **hosted agent** `care-agent` |
| Databricks Genie Space (NL → SQL over certified data) | Genie space `Better2gether Care — Vitals & Fleet` over `better2gether.care_copilot` (fronted by an Agent Bricks Multi-Agent Supervisor endpoint) |
| Unity Catalog governance | Least-privilege UC grants: `USE CATALOG` / `USE SCHEMA` / `SELECT` / `CAN_RUN` on the Genie space / `CAN_QUERY` on the serving endpoints — the caller's identity is what Genie executes as |
| Identity through the chain | **Today:** a scoped service principal (M2M OAuth, secret in Key-Vault-able env) — the Supervisor runs Genie *as the caller*, so its UC grants are the ceiling. **Next step:** per-user Entra **on-behalf-of** passthrough exactly as the article describes, so row-level security and masking resolve per end user. |

The delta between "today" and "next step" is the demo's best conversation starter: the wiring,
tools, and governance surfaces are identical — only the token in the `Authorization` header
changes.

## Layout

```
src/care_harness/
  config.py        # .env-driven settings
  care_copilot.py  # Databricks client: OAuth token cache + Responses payload parsing + the tool
  agent.py         # create_harness_agent wiring (FoundryChatClient + instructions)
  doctor.py        # pre-flight connectivity checks
  main.py          # CLI: interactive / one-shot / scripted demo
tests/             # offline tests for the response parser
```

## Setup

Prereqs: [uv](https://docs.astral.sh/uv/), Azure CLI logged in (`az login`), and the
Databricks service-principal secret from the partner team.

```bash
cp .env.example .env   # then fill in DATABRICKS_CLIENT_SECRET + your Foundry endpoint
uv sync
uv run care-harness --doctor
```

`--doctor` checks all four legs independently (Foundry token, Foundry model call,
Databricks token, Databricks endpoint call) and prints a PASS/FAIL table — run it
before any demo.

## Run

```bash
uv run care-harness                 # interactive chat — one session, multi-turn memory
uv run care-harness --demo          # the 5 scripted demo questions
uv run care-harness --demo -n 4     # just the "money shot" (Genie + KA + web)
uv run care-harness -q "watch-003 keeps disconnecting and the battery dies fast - what's going on?"
```

Demo script (each question exercises a different routing path inside the Care Copilot):

| # | Routes to | Question |
|---|-----------|----------|
| 1 | Knowledge Assistant | What does an SPO2-LOW alert mean, and what should I tell the member? |
| 2 | Genie | How many SPO2-CRIT alerts fired, broken down by region? |
| 3 | Web | What is the normal SpO2 range recommended by major health authorities? |
| 4 | All three | watch-007 oxygen low + disconnects vs. WHO/Mayo guidance — how bad, what to tell them? |
| 5 | Genie + KA | watch-003 keeps disconnecting and the battery dies fast — what's going on? |

## Databricks resources (own workspace — rz-test)

The Care Copilot stack now lives in **your own** workspace (Omri's workspace IP ACL cannot
be opened, so the whole stack was recreated from his `care_copilot_kit`, all via API —
see `databricks/agent_bricks/create_agents_api.sh`; the kit's "Agent Bricks is UI-only"
note is outdated).

| Resource | Value |
|---|---|
| Workspace | `https://adb-7405606288996838.18.azuredatabricks.net` (rz-test, tenant MngEnvMCAP180026) |
| Data | `better2gether.care_copilot.device_registry` (20) / `.vitals_alerts` (629) / `care_kb` volume (8 docs) |
| Genie space | `01f186cb5e8b1ec685de17747041543d` — "Better2gether Care — Vitals & Fleet" |
| Knowledge Assistant | **not used** — KA managed ingestion failed twice in this workspace (index stuck on "pending endpoint provisioning" → FAILED, no error surfaced). The 8 KB docs are instead bundled with the harness and served by the local `search_care_kb` tool. |
| Supervisor (Care Copilot) | tile `cebe7f3f…` → **`mas-cebe7f3f-endpoint`** (Genie-only) ← what the harness calls |
| Service principal | `foundry-care-copilot`, appId `c05dfeba-2e3c-40d4-a1ab-65ea1faa2e4a` (secret in `.env`/`.sp_secret`, untracked) |
| SP grants | CAN_QUERY both endpoints, CAN_RUN Genie space, USE catalog/schema + SELECT, READ volume, CAN_USE warehouse |

## Azure resources (current POC deployment)

| Resource | Value |
|---|---|
| Subscription | `MCAPS-Hybrid-REQ-141134-2026-roeyzalta` (`04197a4f-e8b8-449d-8774-b0a9484fab46`) |
| Resource group | `rg-b2g-care-poc` (eastus2) |
| Foundry account | `b2g-care-foundry` (AIServices, project management enabled) |
| Foundry project | `care-poc` → `https://b2g-care-foundry.services.ai.azure.com/api/projects/care-poc` |
| Model deployment | `gpt-5.4-mini` (GlobalStandard, 50K TPM) |

### RBAC (one-time, required — DONE for roeyzalta)

Control-plane Owner does **not** include data-plane rights. The caller needs a
data-plane role on the Foundry account. **In this MCAPS tenant the built-in role
definitions are stale** — there is no "Azure AI User", and "Azure AI Developer"
lacks the `AIFoundryAPI/*` data actions the *project*-level endpoint requires —
so the role that actually unblocks `FoundryChatClient` is **"Cognitive Services
User"** (it carries the `Microsoft.CognitiveServices/*` wildcard data action):

```bash
az role assignment create --assignee-object-id <your-oid-in-that-tenant> --assignee-principal-type User \
  --role "Cognitive Services User" --subscription 04197a4f-e8b8-449d-8774-b0a9484fab46 \
  --scope "/subscriptions/04197a4f-e8b8-449d-8774-b0a9484fab46/resourceGroups/rg-b2g-care-poc/providers/Microsoft.CognitiveServices/accounts/b2g-care-foundry"
```

("Cognitive Services OpenAI User" + "Azure AI Developer" are also assigned; they
cover the account-level OpenAI surface but not the project surface here.)
Propagation takes 1–3 minutes; verify with `uv run care-harness --doctor`.

## Hosted agent (deployed to Foundry)

The same two-tool harness runs as a **Foundry hosted agent** (`src/care-agent/`,
deployed with `azd deploy`, direct code deploy, Responses protocol):

| | |
|---|---|
| Project | `rg-care-agent-dev` / account `cog-nw4gunns5btr2` / project `care-agent-dev` (northcentralus) |
| Agent | `care-agent` (active) |
| Endpoint | `https://cog-nw4gunns5btr2.services.ai.azure.com/api/projects/care-agent-dev/agents/care-agent/endpoint/protocols/openai/responses?api-version=v1` |
| Invoke | `azd ai agent invoke care-agent "..."` (or POST the endpoint with an `https://ai.azure.com/.default` bearer) |

**Harness-in-hosted-runtime adaptations** (each was a live failure first):
1. `history_provider=InMemoryHistoryProvider(load_messages=False)` — host rejects loading providers.
2. Do **not** set `default_options={"store": False}` — the harness tool loop needs FoundryChatClient's server-side response storage to pair function calls/results (else 400 "No tool call found…").
3. `disable_tool_auto_approval=True` — ToolApprovalMiddleware needs an AgentSession the host doesn't create.
4. `disable_file_memory=True` — container filesystem is read-only.
5. `requirements.txt` must pin the slim `agent-framework-core`/`-foundry`/`-foundry-hosting` trio — the meta package's Linux extras don't resolve in the remote build.
6. This tenant's stale roles: the deploying identity needs **"Cognitive Services User"** on the new account too.

## Known gotchas

* **(Historical) Databricks IP ACL** — Omri's workspace (`adb-984752964297111.11`) has an
  IP access list that could not be opened; that's why the stack was recreated in rz-test.
  Genie serialized_space v2 gotchas hit during the rebuild: no `sample_questions` field,
  and `text_instructions[].id` must be a lowercase 32-hex UUID.
* **Bearer tokens expire hourly** — the tool client caches the SP token and refreshes
  5 min early; never hard-code a minted token.
* **Cross-tenant az auth** — when the Foundry project lives in a different tenant
  than your default `az` context, set `FOUNDRY_SUBSCRIPTION_ID` (preferred) or
  `FOUNDRY_TENANT_ID` in `.env`; the credential passes it through to `az`.
* **Hosted web search is off by default** — the harness's built-in hosted web
  search 404s ("Project not found") on a Foundry project without Bing grounding.
  Demo Q3 routes to the Databricks supervisor's web tool instead. Opt back in
  with `HARNESS_ENABLE_WEB_SEARCH=1` on a grounding-enabled project.
* **Supervisor responses** — the Responses payload interleaves `<name>agent</name>`
  routing markers with text; `care_copilot._extract_answer` returns the final
  synthesized answer plus a routing footer (tested offline in `tests/`).
