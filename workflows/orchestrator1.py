from __future__ import annotations

import base64
import contextlib
import io
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict, Type

import numpy as np
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from workflows.utils import WorkflowUtils  # type: ignore
except Exception:
    WorkflowUtils = None  # type: ignore

try:
    from workflows.config import config  # type: ignore
except Exception:
    config = None  # type: ignore

ROOT = Path(".")
AGENT_PATHS = {
    "admet_mie": ROOT / ".opencode/agents/admet-mie.md",
    "aop_expert": ROOT / ".opencode/agents/aop-expert.md",
    "constructor": ROOT / ".opencode/agents/aop-constructor.md",
    "visuals_agent": ROOT / ".opencode/agents/visuals-agent.md",
}

MAX_ITERATIONS = int(os.environ.get("AOP_MAX_ITERATIONS", "10"))
SIMILARITY_THRESHOLD = float(
    os.environ.get(
        "AOP_SIMILARITY_THRESHOLD",
        str(getattr(config, "similarity_threshold", 0.0) if config is not None else 0.0),
    )
)
MIN_PATHWAY_LENGTH = int(os.environ.get("AOP_MIN_PATHWAY_LENGTH", "5"))
MIN_KE_STEPS = int(os.environ.get("AOP_MIN_KE_STEPS", "3"))
VERBOSE = os.environ.get("AOP_VERBOSE", "false").lower() == "true"
OUTPUT_DIR = Path(os.environ.get("AOP_OUTPUT_DIR", "outputs"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PATHWAY_MEMORY_FILE = OUTPUT_DIR / "pathway_memory.json"
PATHWAY_MEMORY_LIMIT = 200
NO_CANDIDATE_LIMIT = 2

PK_ONLY_TERMS = {
    "cyp", "cyp3a4", "substrate", "metabolism", "metabolic", "clearance",
    "bioavailability", "pharmacokinetic", "exposure", "auc", "cmax", "tmax",
    "half life", "half-life", "hepatic extraction"
}
BIOLOGICAL_TERMS = {
    "toxicity", "neurotoxicity", "hepatotoxicity", "nephrotoxicity", "cardiotoxicity",
    "sedation", "cognitive impairment", "ulcer", "irritation", "injury", "damage",
    "permeability", "inflammation", "apoptosis", "necrosis", "aggregation", "blood flow"
}
AO_READY_TERMS = (
    "erosion", "ulcer", "injury", "damage", "permeability", "blood flow",
    "impairment", "toxicity", "irritation", "necrosis", "apoptosis",
    "cognitive impairment", "sedation", "neurotoxicity", "hepatotoxicity",
    "renal impairment", "platelet aggregation",
    "degeneration", "neuronal degeneration", "neurodegeneration",
)
TERMINAL_KE_TERMS = (
    "erosion", "injury", "damage", "permeability", "ulcer", "toxicity",
    "irritation", "blood flow", "cognitive impairment", "sedation",
    "neurotoxicity", "hepatotoxicity", "renal impairment", "aggregation",
    "degeneration", "neuronal degeneration", "neurodegeneration",
)


class MIE_Info(BaseModel):
    name: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class ADMET_Profile(BaseModel):
    properties: Dict[str, Any] = Field(default_factory=dict)
    liabilities: List[str] = Field(default_factory=list)


class InitialAnalysis(BaseModel):
    target_profile: ADMET_Profile
    mies: List[MIE_Info] = Field(default_factory=list)


class Candidate_Info(BaseModel):
    name: str
    type: str
    confidence: float = Field(ge=0.0, le=1.0)
    similarity: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    reasoning: str = ""


class Candidate_List(BaseModel):
    candidates: List[Candidate_Info] = Field(default_factory=list)


class Similarity_Info(BaseModel):
    name: str
    similarity: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""


class Similarity_List(BaseModel):
    similarities: List[Similarity_Info] = Field(default_factory=list)


class Confidence_Breakdown(BaseModel):
    mie_foundation: float = Field(default=0.0, ge=0.0, le=1.0)
    pathway_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    similarity_consistency: float = Field(default=0.0, ge=0.0, le=1.0)
    pathway_length_penalty: float = Field(default=0.0, ge=0.0, le=1.0)
    pathway_uniqueness: float = Field(default=0.0, ge=0.0, le=1.0)
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "mie_foundation": 0.30,
            "pathway_confidence": 0.40,
            "similarity_consistency": 0.15,
            "pathway_length": 0.05,
            "pathway_uniqueness": 0.10,
        }
    )


class PathwayDecision(BaseModel):
    selected_candidate: Optional[Candidate_Info] = None
    updated_pathway: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_breakdown: Confidence_Breakdown = Field(default_factory=Confidence_Breakdown)
    uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    decision_risk: str = "medium"
    next_action: str = "expand"
    is_ao_reached: bool = False
    termination_reason: str = ""
    decision_reason: str = ""
    rejected_candidates: List[Dict[str, Any]] = Field(default_factory=list)


class AOPState(TypedDict, total=False):
    chemical: str
    messages: List[Dict[str, Any]]
    reference_files: Dict[str, str]
    data: Dict[str, Any]
    AOP_pathways: List[Dict[str, Any]]
    candidates: List[Dict[str, Any]]
    similarity_scores: List[Dict[str, Any]]
    MIEs: List[Dict[str, Any]]
    current_node_type: str
    confidence_score: float
    confidence_breakdown: Dict[str, Any]
    uncertainty: float
    decision_risk: str
    next_action: str
    decision_reason: str
    rejected_candidates: List[Dict[str, Any]]
    provenance: List[Dict[str, Any]]
    is_ao_reached: bool
    termination_reason: str
    iteration_count: int
    previous_pathway_length: int
    start_time: float
    last_progress_update: float
    visualization_path: str
    critic_flags: Dict[str, Any]
    critic_reason: str
    no_candidate_cycles: int


# -------------------------
# Helpers
# -------------------------

def log(message: str) -> None:
    if VERBOSE:
        print(message)


def safe_read(path: Path) -> str:
    return path.read_text() if path.exists() else ""


AGENT_PROMPTS = {name: safe_read(path) for name, path in AGENT_PATHS.items()}


def _normalize_event_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def extract_json_text(text: str) -> str:
    text = text.strip()
    m = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.S)
    return m.group(1).strip() if m else text


def normalize_response(resp: Any) -> Any:
    if hasattr(resp, "model_dump"):
        data = resp.model_dump()
        content = data.get("content")
        if isinstance(content, str):
            text = extract_json_text(content)
            try:
                return json.loads(text)
            except Exception:
                return data
        return data
    if hasattr(resp, "content") and isinstance(getattr(resp, "content"), str):
        text = extract_json_text(getattr(resp, "content"))
        try:
            return json.loads(text)
        except Exception:
            return text
    if isinstance(resp, str):
        text = extract_json_text(resp)
        try:
            return json.loads(text)
        except Exception:
            return text
    return resp


def as_dict(obj: Any) -> Any:
    return obj.model_dump() if hasattr(obj, "model_dump") else normalize_response(obj)


def add_provenance(
    state: AOPState,
    node: str,
    agent: str,
    reason: str = "",
    *,
    confidence: Optional[float] = None,
    similarity: Optional[float] = None,
    source_hint: Optional[str] = None,
    **extra: Any,
) -> None:
    entry: Dict[str, Any] = {"node": node, "agent": agent, "reason": reason, "timestamp": time.time()}
    if confidence is not None:
        entry["confidence"] = float(confidence)
    if similarity is not None:
        entry["similarity"] = float(similarity)
    if source_hint:
        entry["source_hint"] = source_hint
    if extra:
        entry.update(extra)
    state.setdefault("provenance", []).append(entry)


def pathway_events(pathway: List[Dict[str, Any]]) -> List[str]:
    out: List[str] = []
    for step in pathway or []:
        if isinstance(step, dict):
            event = _normalize_event_text(step.get("event", ""))
            if event:
                out.append(event)
    return out


def pathway_signature(pathway: List[Dict[str, Any]]) -> str:
    return " > ".join(pathway_events(pathway))


def pathway_token_set(pathway: List[Dict[str, Any]]) -> set[str]:
    stop = {"a", "an", "and", "of", "the", "to", "in", "for", "with", "via", "by", "from"}
    tokens: set[str] = set()
    for event in pathway_events(pathway):
        for token in event.split():
            if token not in stop:
                tokens.add(token)
    return tokens


def load_pathway_memory() -> List[Dict[str, Any]]:
    if not PATHWAY_MEMORY_FILE.exists():
        return []
    try:
        data = json.loads(PATHWAY_MEMORY_FILE.read_text())
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_pathway_memory(entry: Dict[str, Any]) -> None:
    memory = load_pathway_memory()
    memory.append(entry)
    memory = memory[-PATHWAY_MEMORY_LIMIT:]
    PATHWAY_MEMORY_FILE.write_text(json.dumps(memory, indent=2))


def max_template_overlap(pathway: List[Dict[str, Any]], memory: Optional[List[Dict[str, Any]]] = None) -> float:
    memory = load_pathway_memory() if memory is None else memory
    current = pathway_token_set(pathway)
    if not current or not memory:
        return 0.0
    best = 0.0
    for item in memory:
        tokens = set(item.get("tokens", [])) if isinstance(item, dict) else set()
        if not tokens:
            sig = item.get("signature", "") if isinstance(item, dict) else ""
            tokens = set(sig.split())
        union = current | tokens
        if not union:
            continue
        j = len(current & tokens) / len(union)
        if j > best:
            best = j
    return float(best)


def pathway_uniqueness_score(pathway: List[Dict[str, Any]], memory: Optional[List[Dict[str, Any]]] = None) -> float:
    return float(np.clip(1.0 - max_template_overlap(pathway, memory), 0.0, 1.0))


def pathway_generic_score(pathway: List[Dict[str, Any]]) -> float:
    events = pathway_events(pathway)
    if not events:
        return 1.0
    generic_terms = ("generic", "class level", "broad mechanism", "non specific", "shared target class")
    generic_hits = sum(1 for e in events if any(term in e for term in generic_terms))
    diversity = len(pathway_token_set(pathway)) / max(sum(len(e.split()) for e in events), 1)
    return float(np.clip(0.55 * (generic_hits / max(len(events), 1)) + 0.45 * (1.0 - diversity), 0.0, 1.0))


def pathway_depth_ok(pathway: List[Dict[str, Any]]) -> bool:
    return len(pathway) >= MIN_PATHWAY_LENGTH and sum(1 for s in pathway if isinstance(s, dict) and str(s.get("type", "")).upper() == "KE") >= MIN_KE_STEPS


def pathway_is_pk_only(pathway: List[Dict[str, Any]]) -> bool:
    events = pathway_events(pathway)
    return bool(events) and all(any(term in e for term in PK_ONLY_TERMS) for e in events)


def pathway_is_terminal_ke(pathway: List[Dict[str, Any]]) -> bool:
    last = pathway[-1] if pathway and isinstance(pathway[-1], dict) else {}
    last_type = str(last.get("type", "")).upper()
    last_event = _normalize_event_text(last.get("event", ""))
    return last_type == "KE" and any(term in last_event for term in TERMINAL_KE_TERMS)


def pathway_is_ao_ready(pathway: List[Dict[str, Any]]) -> bool:
    if not pathway:
        return False
    last = pathway[-1] if isinstance(pathway[-1], dict) else {}
    last_type = str(last.get("type", "")).upper()
    last_event = _normalize_event_text(last.get("event", ""))
    return last_type == "AO" or any(term in last_event for term in AO_READY_TERMS)


def liabilities_are_pk_only(liabilities: List[str]) -> bool:
    vals = [str(x).strip() for x in liabilities if str(x).strip()]
    if not vals:
        return False
    has_pk = any(any(term in _normalize_event_text(v) for term in PK_ONLY_TERMS) for v in vals)
    has_bio = any(any(term in _normalize_event_text(v) for term in BIOLOGICAL_TERMS) for v in vals)
    return has_pk and not has_bio


def infer_terminal_ao(state: AOPState) -> str:
    chem = state.get("chemical", "").lower()
    target_profile = state.get("data", {}).get("target_profile", {})
    liabilities = [str(x).lower() for x in target_profile.get("liabilities", [])] if isinstance(target_profile, dict) else []
    last = state.get("AOP_pathways", [])[-1] if state.get("AOP_pathways") and isinstance(state.get("AOP_pathways", [])[-1], dict) else {}
    last_event = _normalize_event_text(last.get("event", ""))
    if any("gastro" in x or "gi" in x for x in liabilities) or "gastric" in last_event or "mucosal" in last_event:
        return "Gastric ulceration"
    if any("cognitive" in x or "cns" in x or "neuro" in x for x in liabilities) or any(x in chem for x in ("toluene", "xylene", "benzene")):
        return "Cognitive impairment"
    if any("hepatic" in x or "liver" in x for x in liabilities):
        return "Hepatotoxicity"
    if any("renal" in x or "kidney" in x for x in liabilities):
        return "Renal impairment"
    if any("platelet" in x or "aggregation" in x for x in liabilities):
        return "Reduced platelet aggregation"
    return liabilities[0].title() if liabilities else "Adverse outcome"


def pathway_review(state: AOPState, pathway: Optional[List[Dict[str, Any]]] = None, memory: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    pathway = state.get("AOP_pathways", []) if pathway is None else pathway
    if state.get("data", {}).get("pk_only_liability", False):
        return {
            "should_expand": False,
            "reason": "PK-only liability detected; no AOP pathway should be expanded.",
            "template_overlap": 0.0,
            "pathway_uniqueness": 1.0,
            "generic_score": 1.0,
            "near_terminal": False,
            "terminal_ke": False,
            "pk_only": True,
        }
    if memory is None:
        memory = load_pathway_memory()
    overlap = max_template_overlap(pathway, memory)
    uniqueness = pathway_uniqueness_score(pathway, memory)
    generic = pathway_generic_score(pathway)
    last = pathway[-1] if pathway and isinstance(pathway[-1], dict) else {}
    last_type = str(last.get("type", "")).upper()
    last_event = _normalize_event_text(last.get("event", ""))
    near_terminal = last_type == "KE" and any(term in last_event for term in TERMINAL_KE_TERMS)
    ke_count = sum(1 for s in pathway if isinstance(s, dict) and str(s.get("type", "")).upper() == "KE")
    terminal_ke = pathway_is_terminal_ke(pathway)
    ao_ready = pathway_is_ao_ready(pathway)

    should_expand = (
        (len(pathway) < MIN_PATHWAY_LENGTH and not terminal_ke)
        or (ke_count < MIN_KE_STEPS and not terminal_ke)
        or overlap >= 0.78
        or generic >= 0.60
        or (near_terminal and not ao_ready and not terminal_ke)
    )

    if len(pathway) < MIN_PATHWAY_LENGTH and not terminal_ke:
        reason = "Pathway is still too shallow"
    elif ke_count < MIN_KE_STEPS and not terminal_ke:
        reason = "Pathway is still too shallow"
    elif overlap >= 0.78:
        reason = "Pathway template overlap is too high"
    elif generic >= 0.60:
        reason = "Pathway looks too generic"
    elif near_terminal and not ao_ready and not terminal_ke:
        reason = "Pathway is near-terminal and should expand one more step"
    else:
        reason = ""

    return {
        "should_expand": should_expand,
        "reason": reason,
        "template_overlap": float(overlap),
        "pathway_uniqueness": float(uniqueness),
        "generic_score": float(generic),
        "near_terminal": bool(near_terminal),
        "terminal_ke": bool(terminal_ke),
    }


def critic_review(state: AOPState, pathway: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    review = pathway_review(state, pathway)
    pathway = state.get("AOP_pathways", []) if pathway is None else pathway
    last = pathway[-1] if pathway and isinstance(pathway[-1], dict) else {}
    last_type = str(last.get("type", "")).upper()
    flags = {
        "template_overlap": float(review.get("template_overlap", 0.0)),
        "pathway_uniqueness": float(review.get("pathway_uniqueness", 0.0)),
        "generic_score": float(review.get("generic_score", 0.0)),
        "near_terminal": bool(review.get("near_terminal", False)),
        "terminal_ke": bool(review.get("terminal_ke", False)),
        "ao_too_early": False,
        "template_reuse": False,
        "premature_termination": False,
    }
    if state.get("is_ao_reached") and not pathway_depth_ok(pathway):
        flags["ao_too_early"] = True
    if state.get("next_action") == "terminate" and last_type != "AO":
        flags["premature_termination"] = True
    if flags["template_overlap"] >= 0.78 and len(pathway) >= max(3, MIN_PATHWAY_LENGTH - 1):
        flags["template_reuse"] = True

    next_action = state.get("next_action", "expand")
    termination_reason = state.get("termination_reason", "")
    if flags["ao_too_early"] or flags["premature_termination"]:
        next_action = "expand"
        termination_reason = review.get("reason") or "Critic forced expansion: pathway is not ready to terminate"
    elif flags["template_reuse"] and not pathway_is_ao_ready(pathway):
        next_action = "expand"
        termination_reason = "Critic forced expansion: pathway template reuse is too high"
    elif flags["near_terminal"] and not pathway_is_terminal_ke(pathway):
        next_action = "expand"
        termination_reason = "Critic requested one more expansion before termination"

    return {
        "critic_flags": flags,
        "next_action": next_action,
        "termination_reason": termination_reason,
        "should_expand": review.get("should_expand", False),
        "reason": review.get("reason", ""),
    }


def calculate_confidence_metrics(state: AOPState) -> Dict[str, float]:
    mies = state.get("MIEs", [])
    mie_foundation = float(np.mean([m.get("confidence", 0.0) for m in mies if isinstance(m, dict)])) if mies else 0.0
    mie_foundation *= max(0.7, 1.0 - state.get("iteration_count", 0) * 0.05)

    pathway = state.get("AOP_pathways", [])
    scores = [s.get("score", 0.0) for s in pathway if isinstance(s, dict)]
    if scores:
        w = np.exp(np.linspace(-1, 0, len(scores)))
        w /= w.sum()
        pathway_confidence = float(np.dot(scores, w))
    else:
        pathway_confidence = 0.0

    sim = [s.get("similarity", 0.0) for s in state.get("similarity_scores", []) if isinstance(s, dict)]
    similarity_consistency = float(max(0.0, 1.0 - np.std(sim))) if len(sim) > 1 else (0.5 if len(sim) == 1 else 0.0)
    n = len(pathway)
    pathway_length_penalty = 1.0 if n <= 5 else max(0.5, 1.0 - (n - 5) * 0.1) if n <= 10 else 0.2
    return {
        "mie_foundation": float(mie_foundation),
        "pathway_confidence": float(pathway_confidence),
        "similarity_consistency": float(similarity_consistency),
        "pathway_length_penalty": float(pathway_length_penalty),
    }


def build_local_confidence_breakdown(state: AOPState, pathway: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    local_state = dict(state)
    if pathway is not None:
        local_state["AOP_pathways"] = pathway
    metrics = calculate_confidence_metrics(local_state)
    uniqueness = pathway_uniqueness_score(local_state.get("AOP_pathways", []), load_pathway_memory())
    metrics["pathway_uniqueness"] = float(uniqueness)
    weights = {
        "mie_foundation": 0.30,
        "pathway_confidence": 0.40,
        "similarity_consistency": 0.15,
        "pathway_length": 0.05,
        "pathway_uniqueness": 0.10,
    }
    breakdown = {
        "mie_foundation": float(metrics.get("mie_foundation", 0.0)),
        "pathway_confidence": float(metrics.get("pathway_confidence", 0.0)),
        "similarity_consistency": float(metrics.get("similarity_consistency", 0.0)),
        "pathway_length_penalty": float(metrics.get("pathway_length_penalty", 0.0)),
        "pathway_uniqueness": float(metrics.get("pathway_uniqueness", 0.0)),
        "weights": weights,
    }
    breakdown["local_confidence_score"] = local_confidence_from_breakdown(breakdown)
    return breakdown


def local_confidence_from_breakdown(breakdown: Dict[str, Any]) -> float:
    weights = breakdown.get("weights", {}) or {}
    score = (
        breakdown.get("mie_foundation", 0.0) * weights.get("mie_foundation", 0.0)
        + breakdown.get("pathway_confidence", 0.0) * weights.get("pathway_confidence", 0.0)
        + breakdown.get("similarity_consistency", 0.0) * weights.get("similarity_consistency", 0.0)
        + breakdown.get("pathway_length_penalty", 0.0) * weights.get("pathway_length", 0.0)
        + breakdown.get("pathway_uniqueness", 0.0) * weights.get("pathway_uniqueness", 0.0)
    )
    return float(np.clip(score, 0.0, 1.0))


def compute_final_confidence(metrics: Dict[str, float]) -> float:
    w = {"mie_foundation": 0.30, "pathway_confidence": 0.40, "similarity_consistency": 0.15, "pathway_length": 0.05, "pathway_uniqueness": 0.10}
    score = (
        metrics.get("mie_foundation", 0.0) * w["mie_foundation"]
        + metrics.get("pathway_confidence", 0.0) * w["pathway_confidence"]
        + metrics.get("similarity_consistency", 0.0) * w["similarity_consistency"]
        + metrics.get("pathway_length_penalty", 0.0) * w["pathway_length"]
        + metrics.get("pathway_uniqueness", 0.0) * w["pathway_uniqueness"]
    )
    return float(np.clip(score, 0.0, 1.0))


# -------------------------
# Agent runtime
# -------------------------

def run_agent(agent_name: str, prompt: str, structured_output: Optional[Type[BaseModel]] = None) -> Any:
    if agent_name not in AGENT_PROMPTS:
        raise ValueError(f"Unknown agent: {agent_name}")
    full_prompt = f"{AGENT_PROMPTS[agent_name]}\n\n{prompt}".strip()
    if WorkflowUtils is None:
        raise RuntimeError("workflows.utils.WorkflowUtils is not available.")

    method_name = "run_agent" if hasattr(WorkflowUtils, "run_agent") else None
    if not method_name:
        for m in ("invoke_agent", "call_agent", "execute_agent"):
            if hasattr(WorkflowUtils, m):
                method_name = m
                break
    if not method_name:
        raise RuntimeError("No compatible agent execution hook found on WorkflowUtils.")

    method = getattr(WorkflowUtils, method_name)
    try:
        with contextlib.ExitStack() as stack:
            if not VERBOSE:
                stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
            return method(agent_name=agent_name, prompt=full_prompt, structured_output=structured_output) if structured_output is not None else method(agent_name=agent_name, prompt=full_prompt)
    except TypeError:
        return method(agent_name, full_prompt, structured_output) if structured_output is not None else method(agent_name, full_prompt)
    except Exception as e:
        raise RuntimeError(f"Agent execution failed: {e}")


# -------------------------
# Initial state and nodes
# -------------------------

def initial_state() -> AOPState:
    return {
        "chemical": "",
        "messages": [],
        "reference_files": AGENT_PROMPTS.copy(),
        "data": {},
        "AOP_pathways": [],
        "candidates": [],
        "similarity_scores": [],
        "MIEs": [],
        "current_node_type": "MIE",
        "confidence_score": 0.0,
        "confidence_breakdown": {},
        "uncertainty": 0.0,
        "decision_risk": "medium",
        "next_action": "expand",
        "decision_reason": "",
        "rejected_candidates": [],
        "provenance": [],
        "is_ao_reached": False,
        "termination_reason": "",
        "iteration_count": 0,
        "previous_pathway_length": 0,
        "start_time": 0.0,
        "last_progress_update": 0.0,
        "critic_flags": {},
        "critic_reason": "",
        "no_candidate_cycles": 0,
    }


def Initial_ADMET_node(state: AOPState) -> AOPState:
    chem = state.get("chemical", "").strip()
    prompt = (
        f"Chemical: {chem}\n\n"
        "Return ONLY structured JSON matching this schema:\n"
        '{"target_profile":{"properties":{...},"liabilities":[...]},"mies":[{"name":"...","confidence":0.0,"reasoning":"..."}]}\n\n'
        "Use only your provided databases and skills. Do not add prose. "
        "Prefer chemical-specific mechanism evidence over class-level summaries, but do allow valid broad mechanisms such as COX-1 inhibition when the evidence supports them. "
        "If known, include target_class, mechanism_of_action, similar_chemicals, known_targets, and other similarity-relevant context inside target_profile.properties."
    )
    payload = as_dict(run_agent("admet_mie", prompt, InitialAnalysis))
    if not isinstance(payload, dict) or "target_profile" not in payload:
        raise RuntimeError(f"admet_mie returned unexpected output: {payload}")

    state["data"] = {**state.get("data", {}), "target_profile": payload["target_profile"]}
    state["MIEs"] = payload.get("mies", [])
    liabilities = payload["target_profile"].get("liabilities", [])
    state.setdefault("data", {})["pk_only_liability"] = liabilities_are_pk_only(liabilities)
    add_provenance(state, "Initial_ADMET", "admet_mie", "Target profile and initial MIEs extracted", source_hint=chem)
    state["messages"].append({"role": "agent", "agent": "admet_mie", "content": payload})
    state["current_node_type"] = "MIE"
    return state


def _is_placeholder_candidate(candidate: Dict[str, Any]) -> bool:
    name = str(candidate.get("name", "")).lower()
    return not name or any(p in name for p in ("placeholder", "unknown", "none", "n/a", "tbd"))



def candidate_gen_node(state: AOPState) -> AOPState:
    chem = state.get("chemical", "")
    target_profile = state.get("data", {}).get("target_profile", {})
    props = target_profile.get("properties", {}) if isinstance(target_profile, dict) else {}
    liabilities = target_profile.get("liabilities", []) if isinstance(target_profile, dict) else []
    memory = load_pathway_memory()
    review = pathway_review(state, memory=memory)

    if state.get("data", {}).get("pk_only_liability", False):
        state["candidates"] = []
        state["similarity_scores"] = []
        state["next_action"] = "terminate"
        state["termination_reason"] = "PK-only liability detected; no biologically supported AOP pathway should be constructed."
        add_provenance(state, "candidate_gen", "aop_expert", "Stopped: PK-only liability, no AOP candidates generated", source_hint=state.get("chemical", ""), pk_only=True)
        return state

    prompt = (
        f"Chemical: {chem}\n"
        f"Current pathway: {json.dumps(state.get('AOP_pathways', []), indent=2)}\n"
        f"MIEs: {json.dumps(state.get('MIEs', []), indent=2)}\n"
        f"Target ADMET profile: {json.dumps(target_profile, indent=2)}\n"
        f"Similarity-relevant properties: {json.dumps(props, indent=2)}\n"
        f"Known liabilities: {json.dumps(liabilities, indent=2)}\n"
        f"Pathway review: {json.dumps(review, indent=2)}\n\n"
        "Return ONLY structured JSON matching this schema:\n"
        '{"candidates":[{"name":"...","type":"KE|AO","confidence":0.0,"reasoning":"..."}]}\n\n'
        "Use only your provided databases and skills. Do not add prose. "
        "Prefer candidates grounded in documented analogs, shared target class, shared exact mechanism, or strong structural similarity. "
        "If the pathway is shallow or generic, return more intermediate KEs and avoid AO. "
        f"Do not propose AO unless the current pathway already contains at least {MIN_PATHWAY_LENGTH} total nodes and at least {MIN_KE_STEPS} KE steps. "
        "Prefer chemical-specific evidence, but do allow valid mechanisms such as COX-1 inhibition when supported. "
        "Avoid generic family templates; keep the pathway distinct from prior chemicals unless the exact mechanism is supported. "
        "If the current pathway already ends in a chemically specific terminal KE, you may return a final AO completion candidate for this exact chemical."
    )
    payload = as_dict(run_agent("aop_expert", prompt, Candidate_List))
    cands = payload.get("candidates", []) if isinstance(payload, dict) else []

    terminal_ke = pathway_is_terminal_ke(state.get("AOP_pathways", []))
    ao_candidate = None
    if terminal_ke:
        ao_candidate = {
            "name": infer_terminal_ao(state),
            "type": "AO",
            "confidence": 0.92,
            "similarity": 0.90,
            "reasoning": "Chemical-specific AO completion from a terminal KE and target liability.",
        }

    if not cands or all(_is_placeholder_candidate(c) for c in cands):
        if terminal_ke and ao_candidate is not None:
            cands = [ao_candidate]
            payload = {"candidates": cands, "fallback": "terminal_ke_ao_completion"}
        else:
            state["candidates"] = []
            state["similarity_scores"] = []
            state["no_candidate_cycles"] = state.get("no_candidate_cycles", 0) + 1
            state["next_action"] = "terminate"
            state["termination_reason"] = "No chemical-specific candidates generated"
            add_provenance(state, "candidate_gen", "aop_expert", "Stopped: no chemical-specific candidates generated", source_hint=state.get("chemical", ""))
            state["messages"].append({"role": "agent", "agent": "aop_expert", "content": payload})
            return state

    # Strict chemical-specific mode: no local fallback and no orchestrator-injected AO unless terminal KE is already present.
    if terminal_ke and ao_candidate is not None and not any(str(c.get("type", "")).upper() == "AO" for c in cands):
        cands.insert(0, ao_candidate)

    if review.get("should_expand", False) and not terminal_ke:
        cands = [c for c in cands if str(c.get("type", "")).upper() != "AO"]

    cands = [dict(c) for c in cands]
    cands.sort(key=lambda c: float(c.get("similarity") or c.get("confidence") or 0.0), reverse=True)

    if not cands:
        state["candidates"] = []
        state["similarity_scores"] = []
        state["no_candidate_cycles"] = state.get("no_candidate_cycles", 0) + 1
        state["next_action"] = "terminate"
        state["termination_reason"] = "No chemical-specific non-AO candidates generated"
        add_provenance(state, "candidate_gen", "aop_expert", "Stopped: no chemical-specific non-AO candidates generated", source_hint=state.get("chemical", ""))
        state["messages"].append({"role": "agent", "agent": "aop_expert", "content": payload})
        return state

    state["candidates"] = cands
    state["no_candidate_cycles"] = 0
    add_provenance(
        state,
        "candidate_gen",
        "aop_expert",
        f"Generated {len(cands)} candidates",
        source_hint=state.get("chemical", ""),
        pathway_review=review,
    )
    state["messages"].append({"role": "agent", "agent": "aop_expert", "content": payload})
    return state
def similarity_scoring_node(state: AOPState) -> AOPState:
    candidates = state.get("candidates", [])
    if not candidates:
        state["similarity_scores"] = []
        state["no_candidate_cycles"] = state.get("no_candidate_cycles", 0) + 1
        state["next_action"] = "terminate" if state["no_candidate_cycles"] >= NO_CANDIDATE_LIMIT else "expand"
        state["termination_reason"] = state.get("termination_reason") or "No candidates generated"
        add_provenance(state, "Similarity_Scoring", "admet_mie", "No candidates to score", no_candidates=True)
        return state

    target_profile = state.get("data", {}).get("target_profile", {})
    props = target_profile.get("properties", {}) if isinstance(target_profile, dict) else {}
    prompt = (
        f"Chemical: {state.get('chemical', '')}\n"
        f"Candidates to score: {json.dumps(candidates, indent=2)}\n"
        f"Current pathway: {json.dumps(state.get('AOP_pathways', []), indent=2)}\n"
        f"MIEs: {json.dumps(state.get('MIEs', []), indent=2)}\n"
        f"Target ADMET profile: {json.dumps(target_profile, indent=2)}\n"
        f"Similarity-relevant properties: {json.dumps(props, indent=2)}\n"
        f"Similarity threshold: {SIMILARITY_THRESHOLD}\n\n"
        "Return ONLY structured JSON matching this schema:\n"
        '{"similarities":[{"name":"...","similarity":0.0,"reasoning":"..."}]}\n\n'
        "Score candidates using direct chemical similarity, shared target class, shared exact mechanism, shared pharmacophore, and adverse-effect profile. "
        "Do not treat same target class as the same exact mechanism. "
        "Prefer chemical-specific evidence, but allow valid broad mechanisms when supported."
    )
    payload = as_dict(run_agent("admet_mie", prompt, Similarity_List))
    sims = payload.get("similarities", []) if isinstance(payload, dict) else []
    if not sims:
        state["similarity_scores"] = []
        state["no_candidate_cycles"] = state.get("no_candidate_cycles", 0) + 1
        state["next_action"] = "terminate"
        state["termination_reason"] = state.get("termination_reason") or "No candidates scored"
        add_provenance(state, "Similarity_Scoring", "admet_mie", "No candidate similarities returned", no_candidates=True)
        return state

    smap = {s.get("name"): s for s in sims if isinstance(s, dict) and s.get("name")}
    state["similarity_scores"] = sims
    updated = []
    for c in candidates:
        item = dict(c)
        s = smap.get(item.get("name"))
        if s:
            item["similarity"] = s.get("similarity")
            item["similarity_reasoning"] = s.get("reasoning", "")
        updated.append(item)
    state["candidates"] = sorted(updated, key=lambda c: float(c.get("similarity") or c.get("confidence") or 0.0), reverse=True)
    state["no_candidate_cycles"] = 0
    add_provenance(state, "Similarity_Scoring", "admet_mie", f"Scored {len(sims)} candidates")
    state["messages"].append({"role": "agent", "agent": "admet_mie", "content": payload})
    return state


def expand_and_prune_node(state: AOPState) -> AOPState:
    if state.get("data", {}).get("pk_only_liability", False):
        state["candidates"] = []
        state["similarity_scores"] = []
        state["is_ao_reached"] = False
        state["next_action"] = "terminate"
        state["termination_reason"] = "PK-only liability detected; terminating without AOP construction."
        add_provenance(state, "expand", "constructor", "Terminated: PK-only liability, no pathway construction", pk_only=True)
        return state

    candidates = state.get("candidates", [])
    review = pathway_review(state)
    if not candidates:
        state["no_candidate_cycles"] = state.get("no_candidate_cycles", 0) + 1
        state["termination_reason"] = state.get("termination_reason") or "No candidates generated"
        state["is_ao_reached"] = False
        state["next_action"] = "terminate" if state["no_candidate_cycles"] >= NO_CANDIDATE_LIMIT else "expand"
        add_provenance(state, "expand", "constructor", "No candidates available; terminating without generic fallback", pathway_review=review)
        return state

    metrics = calculate_confidence_metrics(state)
    prompt = (
        f"Chemical: {state.get('chemical', '')}\n"
        f"Current pathway: {json.dumps(state.get('AOP_pathways', []), indent=2)}\n"
        f"Candidates: {json.dumps(state.get('candidates', []), indent=2)}\n"
        f"Similarity scores: {json.dumps(state.get('similarity_scores', []), indent=2)}\n"
        f"MIEs: {json.dumps(state.get('MIEs', []), indent=2)}\n"
        f"Target ADMET profile: {json.dumps(state.get('data', {}).get('target_profile', {}), indent=2)}\n"
        f"Iteration: {state.get('iteration_count', 0)}\n"
        f"Max iterations: {MAX_ITERATIONS}\n"
        f"Rejected candidates so far: {json.dumps(state.get('rejected_candidates', []), indent=2)}\n"
        f"Pathway review: {json.dumps(review, indent=2)}\n\n"
        f"Calculated quantitative metrics:\n{json.dumps(metrics, indent=2)}\n\n"
        "Return ONLY structured JSON matching this schema:\n"
        '{"selected_candidate":{"name":"...","type":"KE|AO","confidence":0.0,"similarity":0.0,"reasoning":""},"updated_pathway":[{"event":"...","type":"MIE|KE|AO","score":0.0,"provenance":[]}],"uncertainty":0.0,"decision_risk":"low|medium|high","next_action":"expand|prune|branch|terminate","is_ao_reached":false,"termination_reason":"","decision_reason":"","rejected_candidates":[]}\n\n'
        "Use the provided metrics to guide the decision, but let the orchestrator compute the final confidence locally. "
        "Prefer chemically specific evidence, but allow valid broad mechanisms such as COX-1 inhibition when supported. "
        "If the pathway is near-terminal, choose an AO completion rather than stopping at the last KE."
    )
    payload = as_dict(run_agent("constructor", prompt, PathwayDecision))
    if not isinstance(payload, dict):
        raise RuntimeError(f"aop_constructor returned unexpected output: {payload}")
    decision = PathwayDecision.model_validate(payload)

    # Hard AO trim: nothing after the first AO.
    ao_index = next(
        (i for i, s in enumerate(decision.updated_pathway) if isinstance(s, dict) and str(s.get("type", "")).upper() == "AO"),
        None,
    )
    if ao_index is not None:
        decision.updated_pathway = decision.updated_pathway[: ao_index + 1]
        decision.is_ao_reached = True
        decision.next_action = "terminate"
        decision.termination_reason = decision.termination_reason or "AO reached"

    if decision.is_ao_reached and not pathway_depth_ok(decision.updated_pathway):
        decision.is_ao_reached = False
        decision.next_action = "expand"
        decision.termination_reason = "AO proposed before minimum pathway depth was reached"
        decision.updated_pathway = [s for s in decision.updated_pathway if not (isinstance(s, dict) and str(s.get("type", "")).upper() == "AO")] or state.get("AOP_pathways", [])

    if decision.next_action == "terminate" and review.get("should_expand") and not pathway_is_ao_ready(decision.updated_pathway):
        decision.next_action = "expand"
        decision.termination_reason = review.get("reason") or "Forced expansion: pathway still too shallow for termination"

    state["AOP_pathways"] = decision.updated_pathway
    local_breakdown = build_local_confidence_breakdown(state, decision.updated_pathway)
    state["confidence_score"] = local_breakdown["local_confidence_score"]
    state["confidence_breakdown"] = local_breakdown
    state["uncertainty"] = float(np.clip(1.0 - state["confidence_score"], 0.0, 1.0))
    state["decision_risk"] = "low" if state["confidence_score"] >= 0.75 else ("medium" if state["confidence_score"] >= 0.5 else "high")
    state["next_action"] = decision.next_action if not review.get("should_expand") else "expand"
    state["decision_reason"] = decision.decision_reason or review.get("reason", "")
    state["rejected_candidates"] = decision.rejected_candidates or state.get("rejected_candidates", [])

    last_is_ao = bool(decision.updated_pathway and isinstance(decision.updated_pathway[-1], dict) and str(decision.updated_pathway[-1].get("type", "")).upper() == "AO")
    state["is_ao_reached"] = bool(decision.is_ao_reached or last_is_ao)
    if state["is_ao_reached"] and not pathway_depth_ok(state.get("AOP_pathways", [])):
        state["is_ao_reached"] = False
        state["next_action"] = "expand"
        state["termination_reason"] = "AO rejected because minimum pathway depth was not met"
    else:
        state["termination_reason"] = decision.termination_reason or review.get("reason", "") or ("Adverse Outcome reached" if state["is_ao_reached"] else "")

    if decision.selected_candidate:
        add_provenance(
            state,
            "expand",
            "constructor",
            "Constructor selected the next pathway step",
            confidence=decision.selected_candidate.confidence,
            similarity=decision.selected_candidate.similarity,
            selected_candidate=decision.selected_candidate.model_dump(),
        )

    if review.get("should_expand") and not state["is_ao_reached"]:
        add_provenance(state, "expand", "internal_critic", "Forced expansion due to generic or template-like pathway", pathway_review=review)

    state["current_node_type"] = (
        decision.updated_pathway[-1].get("type", state.get("current_node_type", "MIE"))
        if decision.updated_pathway and isinstance(decision.updated_pathway[-1], dict)
        else state.get("current_node_type", "MIE")
    )
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    state["previous_pathway_length"] = len(decision.updated_pathway)
    state["messages"].append({"role": "agent", "agent": "constructor", "content": payload})
    return state


def critic_node(state: AOPState) -> AOPState:
    review = critic_review(state, state.get("AOP_pathways", []))
    state["critic_flags"] = review.get("critic_flags", {})
    state["critic_reason"] = review.get("reason", "")
    if review.get("next_action"):
        state["next_action"] = review["next_action"]
    if review.get("termination_reason"):
        state["termination_reason"] = review["termination_reason"]
    add_provenance(state, "critic", "internal_critic", "Local verification checkpoint", critic_flags=state["critic_flags"], critic_reason=state["critic_reason"])
    return state


def route_after_critic(state: AOPState):
    if state.get("data", {}).get("pk_only_liability", False):
        return END
    if state.get("is_ao_reached"):
        return "visualize" if pathway_depth_ok(state.get("AOP_pathways", [])) else END
    if state.get("next_action") == "terminate":
        return "visualize" if state.get("AOP_pathways") else END
    if state.get("no_candidate_cycles", 0) >= NO_CANDIDATE_LIMIT:
        state["termination_reason"] = state.get("termination_reason") or "No candidates generated after fallback"
        return "visualize" if state.get("AOP_pathways") else END
    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        state["termination_reason"] = state.get("termination_reason") or "Maximum iterations reached"
        return "visualize" if state.get("AOP_pathways") else END
    return "candidate_gen"


def route_after_expand(state: AOPState):
    pathway = state.get("AOP_pathways", [])
    review = critic_review(state, pathway)

    if state.get("data", {}).get("pk_only_liability", False):
        return END
    if state.get("is_ao_reached"):
        if pathway_depth_ok(pathway):
            return "visualize"
        state["is_ao_reached"] = False
        state["next_action"] = "expand"
        state["termination_reason"] = "AO rejected because pathway is too short"
        return END
    if state.get("no_candidate_cycles", 0) >= NO_CANDIDATE_LIMIT:
        state["termination_reason"] = state.get("termination_reason") or "No candidates generated after fallback"
        return END
    if state.get("next_action") == "terminate" and not review.get("should_expand", False):
        return "visualize" if pathway else END
    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        state["termination_reason"] = state.get("termination_reason") or "Maximum iterations reached"
        return "visualize" if pathway else END
    if review.get("should_expand", False):
        state["next_action"] = "expand"
        state["termination_reason"] = state.get("termination_reason") or review.get("reason", "")
        return "candidate_gen"
    return "candidate_gen"


# -------------------------
# Visualization (agent-saved PNG only)
# -------------------------

def save_png_from_response(response: Any, chemical: str) -> Optional[str]:
    if isinstance(response, dict):
        for key in ("file_path", "path", "output_path", "png_path", "saved_path"):
            value = response.get(key)
            if value and str(value).lower().endswith(".png"):
                return str(value)
        for key in ("png_base64", "image_base64", "base64"):
            value = response.get(key)
            if value:
                out = OUTPUT_DIR / f"{chemical.replace(' ', '_').lower()}_aop_map.png"
                out.write_bytes(base64.b64decode(value))
                return str(out)

    if isinstance(response, str):
        text = extract_json_text(response)
        try:
            parsed = json.loads(text)
            return save_png_from_response(parsed, chemical)
        except Exception:
            if text.strip().lower().endswith(".png"):
                return text.strip()

    return None


def visualize(state: AOPState) -> AOPState:
    pathway = state.get("AOP_pathways", [])
    if not pathway:
        state["termination_reason"] = state.get("termination_reason") or "No pathway to visualize"
        state.setdefault("data", {})["visualization_path"] = ""
        state.setdefault("messages", []).append(
            {"role": "system", "content": "No pathway to visualize; skipping PNG generation."}
        )
        return state

    chem = state.get("chemical", "unknown").replace(" ", "_").lower()
    output_path = (OUTPUT_DIR / f"{chem}_aop_topological_map.png").resolve()

    graph_spec = {
        "title": f"AOP map for {state.get('chemical')}",
        "chemical": state.get("chemical", ""),
        "pathway": pathway,
        "similarity_scores": state.get("similarity_scores", []),
        "confidence_score": state.get("confidence_score", 0.0),
        "confidence_breakdown": state.get("confidence_breakdown", {}),
        "termination_reason": state.get("termination_reason", "Unknown"),
        "output_path": str(output_path),
        "requirements": {
            "format": "png",
            "layout": "top-down hierarchical",
            "stressor_at_top": True,
            "ao_at_bottom": True,
            "straight_vertical_edges": True,
            "horizontal_split_only_for_branching": True,
            "no_overlapping_text_or_nodes": True,
            "use_agent_runtime_to_render_png": True,
        },
    }

    prompt = (
        "You are the visualization agent. Use the topological-mapping-aop skill to render a real PNG file. "
        "Save it exactly to output_path. Return ONLY JSON with saved_path, status, and message.\n\n"
        f"GRAPH_SPEC_JSON:\n{json.dumps(graph_spec, indent=2)}\n\n"
        f"output_path: {str(output_path)}\n"
        "Do not invent a path. Do not return markdown."
    )

    response = run_agent("visuals_agent", prompt)
    normalized = normalize_response(response)
    saved_path = save_png_from_response(normalized, chem)

    if not saved_path:
        state["termination_reason"] = state.get("termination_reason") or "visuals_agent did not return a PNG path"
        state.setdefault("data", {})["visualization_path"] = ""
        add_provenance(state, "visualize", "visuals_agent", "No PNG path returned", source_hint=str(output_path))
        return state

    saved_path = Path(saved_path)
    if not saved_path.is_absolute():
        saved_path = (Path.cwd() / saved_path).resolve()

    if not saved_path.exists():
        state["termination_reason"] = state.get("termination_reason") or "visuals_agent claimed PNG saved, but file was not written"
        state.setdefault("data", {})["visualization_path"] = ""
        state.setdefault("messages", []).append(
            {"role": "system", "content": f"visuals_agent returned {saved_path}, but the file does not exist."}
        )
        add_provenance(state, "visualize", "visuals_agent", "PNG path returned but file missing", source_hint=str(saved_path))
        return state

    state.setdefault("data", {})["visualization_path"] = str(saved_path)
    state.setdefault("messages", []).append(
        {"role": "agent", "agent": "visuals_agent", "content": {"response": normalized, "saved_path": str(saved_path)}}
    )
    add_provenance(state, "visualize", "visuals_agent", "Visualization saved", source_hint=str(saved_path))
    return state


# -------------------------
# Output & workflow
# -------------------------

def save_results_to_files(result: AOPState):
    out = {
        "chemical": result.get("chemical", ""),
        "pathway": result.get("AOP_pathways", []),
        "final_ao": result.get("is_ao_reached", False),
        "confidence_score": result.get("confidence_score", 0.0),
        "confidence_breakdown": result.get("confidence_breakdown", {}),
        "uncertainty": result.get("uncertainty", 0.0),
        "decision_risk": result.get("decision_risk", "medium"),
        "next_action": result.get("next_action", "expand"),
        "decision_reason": result.get("decision_reason", ""),
        "iteration_count": result.get("iteration_count", 0),
        "termination_reason": result.get("termination_reason", "Unknown"),
        "MIEs": result.get("MIEs", []),
        "similarity_scores": result.get("similarity_scores", []),
        "candidates": result.get("candidates", []),
        "provenance": result.get("provenance", []),
        "visualization_path": result.get("data", {}).get("visualization_path", ""),
        "no_candidate_cycles": result.get("no_candidate_cycles", 0),
        "critic_flags": result.get("critic_flags", {}),
        "critic_reason": result.get("critic_reason", ""),
        "pk_only_liability": result.get("data", {}).get("pk_only_liability", False),
    }
    Path("aop_results.json").write_text(json.dumps(out, indent=2))
    pathway = result.get("AOP_pathways", [])
    if pathway:
        save_pathway_memory({
            "chemical": result.get("chemical", ""),
            "signature": pathway_signature(pathway),
            "tokens": sorted(pathway_token_set(pathway)),
            "length": len(pathway),
            "final_ao": result.get("is_ao_reached", False),
            "confidence_score": result.get("confidence_score", 0.0),
            "termination_reason": result.get("termination_reason", ""),
            "timestamp": time.time(),
        })


def build_workflow():
    w = StateGraph(AOPState)
    w.add_node("Initial_ADMET", Initial_ADMET_node)
    w.add_node("candidate_gen", candidate_gen_node)
    w.add_node("Similarity_Scoring", similarity_scoring_node)
    w.add_node("expand", expand_and_prune_node)
    w.add_node("critic", critic_node)
    w.add_node("visualize", visualize)
    w.add_edge(START, "Initial_ADMET")
    w.add_edge("Initial_ADMET", "candidate_gen")
    w.add_edge("candidate_gen", "Similarity_Scoring")
    w.add_edge("Similarity_Scoring", "expand")
    w.add_edge("expand", "critic")
    w.add_conditional_edges("critic", route_after_critic)
    w.add_edge("visualize", END)
    return w.compile()


def main():
    chain = build_workflow()
    state = initial_state()
    chemical_name = input("Enter the name of the chemical: ").strip()
    if not chemical_name:
        print("Error: Chemical name cannot be empty.")
        raise SystemExit(1)

    state["chemical"] = chemical_name
    state["start_time"] = time.time()
    state["last_progress_update"] = state["start_time"]

    print("Starting workflow execution...")
    print(f"Processing chemical: {chemical_name}")

    try:
        result = chain.invoke(state)
        print(f"\nWorkflow completed in {time.time() - state['start_time']:.2f} seconds!")
        print(f"Pathway length: {len(result.get('AOP_pathways', []))}")
        print(f"Final confidence score: {result.get('confidence_score', 0.0):.2f}")
        print(f"Uncertainty: {result.get('uncertainty', 0.0):.2f}")
        print(f"Decision risk: {result.get('decision_risk', 'medium')}")
        print(f"Termination reason: {result.get('termination_reason', 'Unknown')}")

        print("\n=== TOTAL CONFIDENCE ===")
        print(f"Total Confidence Score: {result.get('confidence_score', 0.0):.3f}")

        print("\n=== AOP PATHWAY ===")
        for i, node in enumerate(result.get("AOP_pathways", []), start=1):
            print(f"{i}. {node.get('event')} [{node.get('type')}] score={node.get('score', 0.0)}")

        print("\n=== CONFIDENCE BREAKDOWN ===")
        for key, value in result.get("confidence_breakdown", {}).items():
            if isinstance(value, (int, float)):
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value}")

        print("\n=== FINAL AO STATUS ===")
        print("AO reached:", result.get("is_ao_reached", False))
        print("Next action:", result.get("next_action", "expand"))
        print("Decision reason:", result.get("decision_reason", ""))

        print("\n=== ADMET PROPERTIES ===")
        admet_profile = result.get("data", {}).get("target_profile", {})
        if admet_profile:
            for prop, value in admet_profile.get("properties", {}).items():
                print(f"{prop}: {value}")
            if admet_profile.get("liabilities"):
                print("Liabilities:", ", ".join(admet_profile.get("liabilities", [])))

        if result.get("AOP_pathways"):
            last = result["AOP_pathways"][-1]
            print("Final event:", last.get("event"))
            print("Final event type:", last.get("type"))

        print("\n=== SUMMARY ===")
        print(f"Chemical: {result.get('chemical', 'Unknown')}")
        print(f"Total Confidence: {result.get('confidence_score', 0.0):.3f}")
        print(f"Adverse Outcome Reached: {result.get('is_ao_reached', False)}")
        print(f"Pathway Length: {len(result.get('AOP_pathways', []))}")
        print("Visualization saved to:", result.get("data", {}).get("visualization_path", "Not saved"))

        save_results_to_files(result)
    except Exception as e:
        print(f"Error during workflow execution: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
