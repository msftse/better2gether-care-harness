# 15-Minute Session

## Title
**"Ask the Data, Keep the Governance": An Agent Framework Harness on Azure AI Foundry with Databricks Genie as a Tool**

## Abstract (for the agenda)
Business users ask "why did X drop?" in chat; the answers live in governed Gold tables in
Databricks. The tempting shortcut — an agent that writes its own SQL with a god-mode service
principal — breaks the moment security reviews it. This session shows the pattern that survives:
a **Microsoft Agent Framework harness** running on **Azure AI Foundry** (locally *and* as a
Foundry-hosted agent) that treats a **Databricks Genie Space** as a first-class tool, while
**Unity Catalog** stays the single source of truth for who sees what. Everything shown is a
working POC built in one day — including the honest parts: what broke, which RBAC roles actually
matter, and what it takes to put a "batteries-included" harness inside a hosted container.
Based on the pattern popularized by Pablo Castaño's article *"Microsoft Foundry + Databricks
Genie: the agent pattern that respects Unity Catalog."*

## Audience & takeaways
Solution architects and engineers integrating Azure AI Foundry with Databricks. They leave with:
1. A reference architecture where the agent **borrows** data access instead of owning it.
2. A working repo they can clone (harness CLI + hosted agent + Genie/Agent Bricks build scripts — all API, no UI).
3. The six real-world traps (RBAC data actions, hosted-runtime constraints, dependency pinning) and their fixes.

## Slide-by-slide (15:00)

| # | Time | Slide | Content / talking points |
|---|------|-------|--------------------------|
| 1 | 0:00–1:00 | **The two-day Jira ticket** | The bottleneck: every business question becomes a BI ticket. The answer already exists in a governed Gold table. What if the agent could just… ask? |
| 2 | 1:00–2:30 | **The wrong way & the right way** | Wrong: one agent + service principal that can read everything → hallucinated SQL + shadow permissions + audit nightmare. Right (article's pattern diagram): conversation agent ⟶ Genie Space ⟶ Unity Catalog decides. The agent never writes SQL; governance is never duplicated. |
| 3 | 2:30–4:00 | **Architecture of this POC** | The repo's mermaid diagram: Agent Framework **harness** (tool loop, plan/execute, compaction, OTel — all defaults) on Foundry gpt-5.4-mini; two tools: `ask_care_copilot` (Genie via Agent Bricks supervisor) + `search_care_kb` (SOP docs). Same code runs as CLI and as a **Foundry hosted agent**. |
| 4 | 4:00–5:00 | **What Genie brings** | NL→SQL over *certified* tables with table/column comments as semantics. Show the generated SQL from the demo: correct join, correct filter, stated grain. The agent consumes answers, not schemas. |
| 5 | 5:00–7:30 | **LIVE DEMO 1 — the money-shot** | `care-harness --demo -n 4`: "watch-007 oxygen low + disconnecting — how bad, vs. WHO guidance, what do I tell them?" Watch the harness plan, call both tools, and produce a cited care briefing. Point out the routing footer (which sub-agents Genie/KB were consulted). |
| 6 | 7:30–9:00 | **LIVE DEMO 2 — hosted in Foundry** | Same agent, deployed: `azd ai agent invoke care-agent "SPO2-CRIT by region?"` → 87 alerts, 5 regions, from inside Foundry's managed runtime. One `azure.yaml`, `azd provision`, `azd deploy`. |
| 7 | 9:00–10:30 | **Identity: the whole point** | Article's runtime-sequence diagram. Today: scoped SP (M2M) — supervisor runs Genie *as the caller*, UC grants are the ceiling; offboarding = delete one SP. Next: **Entra OBO passthrough** → row-level security resolves per end user; VP and rep ask the same question, get different rows. Only the bearer token changes. |
| 8 | 10:30–12:00 | **The six traps** (what actually broke) | 1) Tenant role definitions can be stale — "Cognitive Services User" wildcard saved us twice. 2) Hosted agents need eligible regions. 3) Meta-package Linux extras don't pip-resolve remotely. 4) Harness history provider vs. hosting-managed history. 5) Approval middleware needs a session. 6) Read-only container FS vs. file memory. Each: one line of config once you know. |
| 9 | 12:00–13:30 | **Everything is API** | Agent Bricks "UI-only" is outdated: KA + Multi-Agent Supervisor created via REST (`/api/2.1/knowledge-assistants`, `/api/2.0/multi-agent-supervisors`). Genie space via `serialized_space`. Whole environment rebuilt from a kit in ~1 hour — reproducible, reviewable, CI-able. |
| 10 | 13:30–15:00 | **Wrap + call to action** | Recap the three principles: agents borrow access, governance stays in UC, everything scripted. Repo: `msftse/better2gether-care-harness`. Eval suite + continuous monitoring next. Q&A pointer. |

## Demo fallback plan
If live demo fails: the README has full transcripts of all five demo questions; slides 5–6 get
static screenshots. The `--doctor` pre-flight table is itself a good 30-second slide if the
network misbehaves.

## Credits
Pattern and diagrams: [Pablo Castaño's article](https://medium.com/@depablocastano/microsoft-foundry-databricks-genie-the-agent-pattern-that-respects-unity-catalog-a5a06852c5f9).
Care Copilot scenario & kit: Omri (Databricks). Implementation: this repo.
