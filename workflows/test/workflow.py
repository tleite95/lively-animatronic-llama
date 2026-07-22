from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, Literal, Dict, Any

from langgraph.graph import StateGraph, END

from opencode_ai import Opencode


BASE = Path(__file__).parent
AGENTS = BASE / "agents"
SKILLS = BASE / "skills"

@dataclass
class Definition:
    name: str
    body: str
    path: Path


def load_md(path: Path) -> Definition:
    text = path.read_text(encoding="utf-8")
    name = path.stem
    m = re.search(r"^name:\s*(.+)$", text, re.M)
    if m:
        name = m.group(1).strip()
    return Definition(name=name, body=text, path=path)


def load_bank(folder: Path) -> Dict[str, Definition]:
    if not folder.exists():
        return {}
    return {p.stem: load_md(p) for p in folder.glob("*.md")}


agents = load_bank(AGENTS)
skills = load_bank(SKILLS)

class State(TypedDict):
    user_input: str
    route: Literal["research", "code", "write", "general"]
    agent_name: str
    skill_name: str
    draft: str
    result: str

def route_node(state: State) -> dict:
    text = state["user_input"].lower()
    if any(k in text for k in ["paper", "cite", "research", "source"]):
        return {"route": "research", "agent_name": "researcher", "skill_name": "cite_sources"}
    if any(k in text for k in ["code", "python", "bug", "fix", "refactor"]):
        return {"route": "code", "agent_name": "engineer", "skill_name": "code_review"}
    if any(k in text for k in ["write", "draft", "email", "doc"]):
        return {"route": "write", "agent_name": "writer", "skill_name": "tone_polish"}
    return {"route": "general", "agent_name": "generalist", "skill_name": "answer_briefly"}


client = Opencode(base_url="http://127.0.0.1:4096")
def opencode_model_call(user_input: str) -> str:
    session = client.session.create()
    result = client.session.chat(
        id=session.id,
        provider_id="ssec-litellm",
        model_id="devstral-small",
        parts=[{"type": "text", "text": user_input}],
    )

    return result.info.content if hasattr(result.info, "content") else str(result)

def agent_node(state):
    agent = agents.get(state["agent_name"])
    skill = skills.get(state["skill_name"])

    agent_prompt = agent.body if agent else f"# {state['agent_name']}\nDefault agent prompt."
    skill_prompt = skill.body if skill else f"# {state['skill_name']}\nDefault skill prompt."

    prompt = (
        f"AGENT:\n{agent_prompt}\n\n"
        f"SKILL:\n{skill_prompt}\n\n"
        f"INPUT:\n{state['user_input']}\n\n"
        f"Return the final answer only."
    )

    draft = opencode_model_call(prompt)
    return {"draft": draft}

def skill_node(state: State) -> dict:
    # Replace this with a real post-processing step, tool call, or model refinement.
    result = state["draft"].replace("structured response", "final response")
    return {"result": result}

def build_graph():
    g = StateGraph(State)
    g.add_node("route", route_node)
    g.add_node("agent", agent_node)
    g.add_node("skill", skill_node)
    g.set_entry_point("route")
    g.add_edge("route", "agent")
    g.add_edge("agent", "skill")
    g.add_edge("skill", END)
    return g.compile()

if __name__ == "__main__":
    app = build_graph()
    out = app.invoke({
        "user_input": "Help me outline a research workflow with citations.",
        "route": "general",
        "agent_name": "generalist",
        "skill_name": "answer_briefly",
        "draft": "",
        "result": "",
    })
    
    print(out["result"])