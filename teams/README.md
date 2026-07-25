# Care Copilot in Microsoft Teams

Puts the **Foundry-hosted Agent Framework harness** (`care-agent`, with Databricks Genie +
care-KB tools) into Microsoft Teams, adapting the
[msftse/sre-agent-teams-integration](https://github.com/msftse/sre-agent-teams-integration)
bridge pattern from the Azure SRE Agent to an Azure AI Foundry hosted agent.

```
Teams @mention ──▶ Azure Bot Service ──▶ Messages Function (ack fast)
                                              │ storage queue
                                              ▼
                                   ProcessCareQuestion worker
                                              │ POST /agents/care-agent/…/responses
                                              ▼          (managed identity, ai.azure.com)
                                Foundry hosted agent (harness)
                                   ├─ ask_care_copilot ──▶ Databricks Genie (Unity Catalog)
                                   └─ search_care_kb
                                              │ proactive Bot Framework reply
                                              ▼
                                       same Teams thread
```

Key properties inherited from the SRE bridge:
- **One user-assigned managed identity** is both the Bot Service identity
  (`UserAssignedMSI` — no app registration, no client secret) and the credential
  for the Foundry data plane.
- **Queue + proactive replies** decouple Teams' ~15s HTTP window from agent runs
  that take 10–60s; the bot acks instantly ("On it…") and posts the answer when ready.
- **Table storage maps conversation → last `response_id`**, so follow-up questions
  chain through `previous_response_id` and keep context server-side on Foundry.
  `/start` clears the mapping.

## Deploy

```bash
cd teams/iac
cp terraform.tfvars.example terraform.tfvars   # already correct for this POC
terraform init && terraform apply

cd .. && ./deploy.sh
```

`deploy.sh` publishes the .NET 8 isolated Functions app (zip deploy), then renders
`teams-app/manifest.json` with the bot id and zips `care-copilot-teams.zip`.

## Install in Teams

Teams → **Apps → Manage your apps → Upload an app → Upload a custom app** →
pick `teams/care-copilot-teams.zip`. (Requires custom-app upload to be allowed
for your account; a Teams admin can also publish it org-wide.)

Then chat 1:1 with **Care Copilot** or add it to a team and @mention it:

> @Care Copilot how many SPO2-CRIT alerts fired, broken down by region?
> @Care Copilot watch-003 keeps disconnecting and the battery dies fast — what's going on?
> /start   ← reset the conversation context

## Files

```
app/          .NET 8 isolated Functions bridge (Bot handler, queue worker, Foundry client)
iac/          Terraform: identity, storage, Flex Consumption app, Bot Service + Teams channel, RBAC
teams-app/    Teams manifest template + icons  → care-copilot-teams.zip
deploy.sh     publish + zip-deploy + package
```

## Notes

- The bridge identity gets **"Cognitive Services User"** on the Foundry account —
  in this tenant that's the role with the `Microsoft.CognitiveServices/*` wildcard
  data action ("Azure AI User" doesn't exist here). RBAC propagation can take a
  few minutes after `terraform apply`; the first Teams question may fail until it lands.
- Today the bridge calls Foundry with its own managed identity (M2M). The article
  pattern's end state — per-user Entra OBO so Unity Catalog row-level security
  resolves per Teams user — is a Bot Framework SSO + OBO exchange away, and the
  bridge is the right place to add it.
