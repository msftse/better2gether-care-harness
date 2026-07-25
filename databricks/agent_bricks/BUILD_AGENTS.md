# Build the Agents in Agent Bricks (UI)

Agent Bricks agents (Knowledge Assistant, Multi-Agent Supervisor) are created in the
Databricks UI — there is no API/DAB path for them. This takes ~15 minutes. Do it in
**your own workspace** (serverless, Agent Bricks enabled) after the data + Genie space
are in place.

Prerequisites (from earlier steps):
- Data foundation created: `better2gether.care_copilot.device_registry`, `.vitals_alerts`, `.care_kb` volume with 8 docs
- Genie space created (you have its `space_id`)

---

## 1. Knowledge Assistant

**Agent Bricks → Knowledge Assistant → Create**

- **Name:** `Care KB Assistant`
- **Knowledge source:** Volume → `better2gether.care_copilot.care_kb`
- **Description (paste):**
  ```
  Better2gether wearable care knowledge base: alert-code glossary, vitals interpretation,
  connectivity & firmware/OTA SOPs, device setup, warranty/RMA, privacy, and the wellness handbook.
  ```
- **Instructions (paste):**
  ```
  You are Better2gether's Care Knowledge Assistant. Answer care-team questions using only the
  provided documentation.
  - Always cite the source doc (and the TS-code or alert code) you used.
  - Provide wellness guidance only — never a medical diagnosis.
  - For device faults, give the matching TS- procedure and check firmware first: v2.3.8 issues
    are usually fixed by updating to v2.4.1 before an RMA.
  - Be concise and actionable.
  ```
- Click **Create**, then **wait for the document index to finish syncing** (a few minutes).
  Test in its chat: *"What does an SPO2-CRIT alert mean?"* — it should answer from the glossary
  with a citation. Do NOT move on until this works.

---

## 2. Multi-Agent Supervisor

**Agent Bricks → Multi-Agent Supervisor → Create**

- **Name:** `Care Copilot`
- **Description (paste):**
  ```
  Better2gether Care Copilot — combines member and fleet data (Genie), our care documentation
  (Knowledge Assistant), and public health/device references (Web Search) into one cited answer.
  Wellness support, never medical diagnosis.
  ```
- **Add agent 1 — Genie:** paste your Genie `space_id` from the previous step.
  Describe: "our member vitals, alerts, and fleet data."
- **Add agent 2 — Knowledge Assistant:** select `Care KB Assistant`.
  Describe: "how-to guidance, alert meanings, fixes, policies."
- **Add tool 3 — Web Search** (optional): "public info not in our data or docs."
- **Instructions (paste):**
  ```
  You are Better2gether's Care Copilot for care-team agents. You have three tools:
  - Genie: our member and fleet data — vitals, device registry, and vitals_alerts.
  - Knowledge Assistant: our care documentation — alert meanings, fixes, and policies.
  - Web Search: public/external information — clinical guidelines, regulations, and
    comparisons that are NOT in our data or docs.

  Rules:
  - Pick the right tool(s); many questions need more than one. Combine the numbers with the
    meaning and, when relevant, the outside reference.
  - Always cite the source of every part of your answer.
  - Provide wellness guidance only — never a medical diagnosis.
  ```
- Click **Create / Deploy**. When ready, it is served at a Model Serving endpoint named like
  `mas-xxxxxxxx-endpoint` (Serving page). **This endpoint name is what you use from Foundry.**

---

## 3. Demo questions to validate

| Routes to | Question |
|---|---|
| Genie | `How many SPO2-CRIT alerts fired, broken down by region?` |
| KA | `What does an SPO2-LOW alert mean and what should I tell the member?` |
| Web Search | `What is the normal SpO2 range recommended by major health authorities?` |
| All three (money-shot) | `Member watch-007's oxygen readings look low and the watch keeps disconnecting. How do those readings compare to the recommended normal range, how bad is it, and what should I tell them?` |

Once the money-shot returns a combined, cited answer, you're ready for the Foundry connection
(see `foundry/`).
