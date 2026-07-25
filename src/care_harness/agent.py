"""Assemble the Agent Framework harness agent on Azure AI Foundry.

The harness (`create_harness_agent`) wraps the Foundry chat client with the full
batteries-included agentic pipeline — tool-calling loop, todo/plan tracking,
plan/execute modes, file memory, per-call history persistence, compaction, tool
auto-approval, and OpenTelemetry — and we hand it one custom tool: the Databricks
Care Copilot (Genie + Knowledge Assistant + web).
"""

from __future__ import annotations

from agent_framework import create_harness_agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

from .care_copilot import CareCopilotClient, make_care_copilot_tool
from .care_kb import search_care_kb
from .config import Settings

AGENT_NAME = "b2g-care-harness"

AGENT_INSTRUCTIONS = """\
You are the Better2gether care-team copilot. You help human care agents support
members of a wellness program who wear connected health watches (SpO2, heart
rate, battery, connectivity telemetry).

You have two tools:
  1. `ask_care_copilot` — the Better2gether Care Copilot on Databricks (an Agent
     Bricks supervisor over a Genie space). Use it for ALL quantitative questions
     over the live member/fleet data: alert counts, readings for a specific
     device like watch-007, breakdowns by region, firmware campaign candidates.
  2. `search_care_kb` — the program's care documentation: what alert codes mean
     (SPO2-LOW, BATT-CRIT, ...), vitals interpretation, care SOPs and TS-
     troubleshooting procedures, firmware/OTA updates, warranty/RMA, privacy,
     and the wellness handbook. Use it for ANY policy/meaning/how-to question.

For published external guidance (WHO, Mayo Clinic, health authorities), answer
from your general knowledge, say that it is general knowledge, and recommend
verifying against the authority's current published guidance.

Working style:
- For member/device data questions, ALWAYS ground numbers in `ask_care_copilot` —
  never invent telemetry numbers. For policy/meaning, ground in `search_care_kb`.
- Many questions need BOTH tools: get the numbers, then the meaning/procedure.
- Send the Care Copilot complete, self-contained questions (it has no memory of
  this conversation). Batch related sub-questions into one rich question when
  possible.
- For complex asks, plan first: break the request into steps with your todo
  list, then execute.
- Answer as a concise briefing the care agent can act on: what the data shows,
  what it means, what to tell the member, and when to escalate.
- If the Care Copilot returns an ERROR (e.g. the Databricks IP access list is
  blocking this network), report the error honestly and clearly instead of
  guessing an answer.
"""


def build_agent(settings: Settings, *, copilot: CareCopilotClient):
    """Create the harness agent. Caller owns the CareCopilotClient lifecycle."""
    # Selecting by subscription lets `az` pick the right cached identity when the
    # Foundry project lives in a different tenant than the default az context.
    # az accepts subscription OR tenant, not both — subscription wins when set.
    cred_kwargs: dict = {}
    if settings.foundry_subscription:
        cred_kwargs["subscription"] = settings.foundry_subscription
    elif settings.foundry_tenant_id:
        cred_kwargs["tenant_id"] = settings.foundry_tenant_id
    credential = AzureCliCredential(**cred_kwargs)
    chat_client = FoundryChatClient(
        project_endpoint=settings.foundry_project_endpoint,
        model=settings.foundry_model_deployment,
        credential=credential,
    )

    return create_harness_agent(
        chat_client,
        name=AGENT_NAME,
        agent_instructions=AGENT_INSTRUCTIONS,
        tools=[make_care_copilot_tool(copilot), search_care_kb],
        # Token-budget compaction keeps long tool loops inside the context window.
        max_context_window_tokens=settings.max_context_window_tokens,
        max_output_tokens=settings.max_output_tokens,
        # The Databricks supervisor has its own web tool; the harness's hosted
        # web search stays available unless explicitly disabled via env.
        disable_web_search=settings.disable_web_search,
    )
