"""CLI for the Better2gether care harness POC.

    uv run care-harness                       # interactive chat (multi-turn session)
    uv run care-harness -q "..."              # one-shot question
    uv run care-harness --demo                # run the 5 scripted demo questions
    uv run care-harness --demo -n 2           # run just demo question #2
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule

from .agent import build_agent
from .care_copilot import CareCopilotClient
from .config import load_settings

console = Console()

DEMO_QUESTIONS: list[tuple[str, str]] = [
    (
        "Knowledge Assistant only",
        "What does an SPO2-LOW alert mean, and what should I tell the member?",
    ),
    (
        "Genie only",
        "How many SPO2-CRIT alerts fired, broken down by region?",
    ),
    (
        "Web only",
        "What is the normal SpO2 range recommended by major health authorities?",
    ),
    (
        "All three (Genie + KA + web)",
        "Member watch-007's oxygen readings look low and the watch keeps "
        "disconnecting. How do our readings compare to the latest published "
        "guidance from health authorities like the WHO or the Mayo Clinic, how "
        "bad is it, and what should I tell them?",
    ),
    (
        "Combined troubleshooting",
        "watch-003 keeps disconnecting and the battery dies fast - what's going on?",
    ),
]


async def _run_turn(agent, session, question: str) -> None:
    """Stream one agent turn, surfacing tool calls as they happen."""
    console.print(Panel(question, title="care agent asks", border_style="cyan"))
    parts: list[str] = []
    announced: set[str] = set()

    async for update in agent.run(question, stream=True, session=session):
        for content in getattr(update, "contents", []) or []:
            ctype = type(content).__name__
            if "FunctionCall" in ctype or "FunctionApproval" in ctype:
                name = getattr(content, "name", "") or ""
                call_id = getattr(content, "call_id", None) or ""
                key = f"call:{name}:{call_id}"
                if name and key not in announced:
                    announced.add(key)
                    console.print(f"[dim]  ⇢ tool call: [bold]{name}[/bold][/dim]")
            elif "FunctionResult" in ctype:
                call_id = getattr(content, "call_id", None) or ""
                key = f"result:{call_id}"
                if key not in announced:
                    announced.add(key)
                    console.print("[dim]  ⇠ tool result received[/dim]")
            elif "Text" not in ctype and ctype not in announced:
                announced.add(ctype)
                console.print(f"[dim]  · {ctype}[/dim]")
        text = getattr(update, "text", None)
        if text:
            parts.append(text)

    answer = "".join(parts).strip() or "(no text response)"
    console.print(Panel(Markdown(answer), title="harness answers", border_style="green"))


async def run_demo(only: int | None) -> None:
    settings = load_settings()
    copilot = CareCopilotClient(settings)
    try:
        agent = build_agent(settings, copilot=copilot)
        for idx, (label, question) in enumerate(DEMO_QUESTIONS, start=1):
            if only is not None and idx != only:
                continue
            console.print(Rule(f"Demo {idx}/5 — {label}"))
            session = agent.create_session()  # fresh session per scripted question
            await _run_turn(agent, session, question)
    finally:
        await copilot.aclose()


async def run_once(question: str) -> None:
    settings = load_settings()
    copilot = CareCopilotClient(settings)
    try:
        agent = build_agent(settings, copilot=copilot)
        session = agent.create_session()
        await _run_turn(agent, session, question)
    finally:
        await copilot.aclose()


async def run_interactive() -> None:
    settings = load_settings()
    copilot = CareCopilotClient(settings)
    try:
        agent = build_agent(settings, copilot=copilot)
        session = agent.create_session()  # one session -> multi-turn memory
        console.print(
            Panel(
                "Better2gether care harness — Microsoft Agent Framework on Azure AI "
                "Foundry, with the Databricks Care Copilot (Genie + Knowledge "
                "Assistant + web) as a tool.\nType a question, or 'exit' to quit.",
                border_style="magenta",
            )
        )
        while True:
            try:
                question = console.input("[bold cyan]you>[/bold cyan] ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not question or question.lower() in {"exit", "quit"}:
                break
            await _run_turn(agent, session, question)
    finally:
        await copilot.aclose()


def cli() -> None:
    parser = argparse.ArgumentParser(description="Better2gether care harness POC")
    parser.add_argument("-q", "--question", help="ask a single question and exit")
    parser.add_argument("--demo", action="store_true", help="run the scripted demo questions")
    parser.add_argument("-n", type=int, default=None, help="with --demo: run only question N (1-5)")
    parser.add_argument("--doctor", action="store_true", help="run connectivity pre-flight checks")
    args = parser.parse_args()

    try:
        if args.doctor:
            from .doctor import run_doctor

            ok = asyncio.run(run_doctor(load_settings()))
            sys.exit(0 if ok else 1)
        elif args.demo:
            asyncio.run(run_demo(args.n))
        elif args.question:
            asyncio.run(run_once(args.question))
        else:
            asyncio.run(run_interactive())
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    cli()
