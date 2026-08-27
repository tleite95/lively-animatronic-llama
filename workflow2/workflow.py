#!/usr/bin/env python3
"""
Workflow core for the AOP graph.

This module defines the shared state, agent node wrappers, pathway heuristics,
confidence helpers, and output helpers.

The orchestration graph itself should live in orchestrator.py.
"""

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

try:
    from .read_across_tox21 import enrich_read_across_state, summarize_read_across  # type: ignore
except Exception:
    enrich_read_across_state = None  # type: ignore
    summarize_read_across = None  # type: ignore

ROOT = Path(".")
AGENT_PATHS = {
    "admet_mie": ROOT / ".opencode/agents/admet-mie.md",
    "aop_expert": ROOT / ".opencode/agents/aop-expert.md",
    "aop_constructor": ROOT / ".opencode/agents/aop-constructor.md",
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
TEMPLATE_OVERLAP_THRESHOLD = float(os.environ.get("AOP_TEMPLATE_OVERLAP_THRESHOLD", "0.80"))
GENERIC_SCORE_THRESHOLD = float(os.environ.get("AOP_GENERIC_SCORE_THRESHOLD", "0.70"))
NO_PROGRESS_LIMIT = int(os.environ.get("AOP_NO_PROGRESS_LIMIT", "2"))


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
    critic_flags: Dict[str, Any]
    critic_reason: str
    no_candidate_cycles: int
    previous_pathway_signature: str
    no_progress_cycles: int


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
    # More lenient criteria for pathway depth
    # Allow AO if we have at least 2 steps and 1 KE, or 3 steps total
    pathway_len = len(pathway)
    ke_count = sum(1 for s in pathway if isinstance(s, dict) and str(s.get("type", "")).upper() == "KE")
    
    # Accept if we have sufficient pathway length OR sufficient KE steps
    return (pathway_len >= MIN_PATHWAY_LENGTH and ke_count >= MIN_KE_STEPS) or \
           (pathway_len >= 3) or \
           (ke_count >= 1 and pathway_len >= 2)


def pathway_review(state: AOPState, pathway: Optional[List[Dict[str, Any]]] = None, memory: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    pathway = state.get("AOP_pathways", []) if pathway is None else pathway
    if memory is None:
        memory = load_pathway_memory()
    overlap = max_template_overlap(pathway, memory)
    uniqueness = pathway_uniqueness_score(pathway, memory)
    generic = pathway_generic_score(pathway)
    ke_count = sum(1 for s in pathway if isinstance(s, dict) and str(s.get("type", "")).upper() == "KE")

    should_expand = (
        len(pathway) < MIN_PATHWAY_LENGTH
        or ke_count < MIN_KE_STEPS
        or overlap >= TEMPLATE_OVERLAP_THRESHOLD
        or generic >= GENERIC_SCORE_THRESHOLD
    )

    if len(pathway) < MIN_PATHWAY_LENGTH:
        reason = "Pathway is still too shallow"
    elif ke_count < MIN_KE_STEPS:
        reason = "Pathway is still too shallow"
    elif overlap >= TEMPLATE_OVERLAP_THRESHOLD:
        reason = "Pathway template overlap is too high"
    elif generic >= GENERIC_SCORE_THRESHOLD:
        reason = "Pathway looks too generic"
    else:
        reason = ""

    return {
        "should_expand": should_expand,
        "reason": reason,
        "template_overlap": float(overlap),
        "pathway_uniqueness": float(uniqueness),
        "generic_score": float(generic),
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
        "previous_pathway_signature": "",
        "no_progress_cycles": 0,
    }


def Initial_ADMET_node(state: AOPState) -> AOPState:
    chem = state.get("chemical", "").strip()
    prompt = (
        f"Chemical: {chem}\n\n"
        "Return ONLY structured JSON matching this schema:\n"
        '{"target_profile":{"properties":{...},"liabilities":[...]},"mies":[{"name":"...","confidence":0.0,"reasoning":"..."}]}\n\n'
        "AOP_CANDIDATE_PROTOCOL_V2: This is an evidence-only AOP candidate generation pass. Do not reuse read-across analogs as biological events. "
        "Use only your provided databases and skills. Do not add prose. "
        "Prefer chemical-specific mechanism evidence over class-level summaries, but do allow valid broad mechanisms when supported. "
        "If known, include target_class, mechanism_of_action, similar_chemicals, known_targets, and other similarity-relevant context inside target_profile.properties."
    )
    payload = as_dict(run_agent("admet_mie", prompt, InitialAnalysis))
    if not isinstance(payload, dict) or "target_profile" not in payload:
        raise RuntimeError(f"admet_mie returned unexpected output: {payload}")

    state["data"] = {**state.get("data", {}), "target_profile": payload["target_profile"]}
    state["MIEs"] = payload.get("mies", [])
    
    # Print initial ADMET and MIE information
    print(f"\n{'='*60}")
    print(f"INITIAL ADMET ANALYSIS FOR: {chem}")
    print(f"{'='*60}")
    
    mies = payload.get("mies", [])
    if mies:
        print(f"\nIdentified MIE(s):")
        for i, mie in enumerate(mies, 1):
            print(f"  {i}. {mie.get('name', 'Unknown')}")
            print(f"     Confidence: {mie.get('confidence', 0.0)}")
            print(f"     Reasoning: {mie.get('reasoning', 'No reasoning provided')}")
    
    target_profile = payload["target_profile"]
    if isinstance(target_profile, dict):
        props = target_profile.get("properties", {})
        if props:
            print(f"\nTarget profile properties:")
            for prop, value in list(props.items())[:5]:  # Show first 5 properties
                print(f"  {prop}: {value}")
        
        liabilities = target_profile.get("liabilities", [])
        if liabilities:
            print(f"\nKnown liabilities:")
            for liability in liabilities[:3]:  # Show first 3 liabilities
                print(f"  - {liability}")
    
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
    review = pathway_review(state)

    # Use cached read-across results (should already be populated from enrich_read_across_node)
    read_across = state.get("data", {}).get("read_across", {}) if isinstance(state.get("data", {}), dict) else {}
    if (not isinstance(read_across, dict) or not read_across) and enrich_read_across_state is not None:
        try:
            # Check if ctx-python should be used
            use_ctx = os.environ.get("USE_CTX_PYTHON", "false").lower() == "true"
            enrich_read_across_state(state, use_ctx=use_ctx, top_k=int(os.environ.get("READ_ACROSS_TOP_K", "5")))
            read_across = state.get("data", {}).get("read_across", {})
        except Exception as e:
            log(f"Read-across enrichment failed in candidate_gen_node: {e}")
            read_across = {}

    read_across_summary = ""
    read_across_analogs: List[Dict[str, Any]] = []
    read_across_endpoints: List[str] = []
    read_across_evidence: List[str] = []
    if isinstance(read_across, dict) and read_across:
        read_across_summary = summarize_read_across(read_across) if summarize_read_across is not None else str(read_across.get("summary", ""))
        read_across_analogs = read_across.get("analogs", []) if isinstance(read_across.get("analogs", []), list) else []
        read_across_endpoints = read_across.get("matched_endpoints", []) if isinstance(read_across.get("matched_endpoints", []), list) else []
        read_across_evidence = read_across.get("supporting_evidence", []) if isinstance(read_across.get("supporting_evidence", []), list) else []
        
        # Print read-across information
        print(f"\n{'='*60}")
        print(f"READ-ACROSS RESULTS FOR: {chem}")
        print(f"{'='*60}")
        
        if read_across_analogs:
            print(f"\nSimilar molecules found:")
            for i, analog in enumerate(read_across_analogs[:3], 1):
                print(f"  {i}. {analog.get('name', 'Unknown')}")
                print(f"     Similarity: {analog.get('score', 0.0)}")
                if isinstance(analog, dict):
                    reasoning = analog.get('reasoning', '')
                    if reasoning:
                        print(f"     Reasoning: {reasoning[:100]}...")
        
        if read_across_endpoints:
            print(f"\nMatched endpoints:")
            for endpoint in read_across_endpoints[:5]:
                print(f"  - {endpoint}")
        
        if read_across_summary:
            print(f"\nSummary: {read_across_summary}")

    prompt = (
        f"Chemical: {chem}\n"
        f"Current pathway: {json.dumps(state.get('AOP_pathways', []), indent=2)}\n"
        f"MIEs: {json.dumps(state.get('MIEs', []), indent=2)}\n"
        f"Target profile: {json.dumps(target_profile, indent=2)}\n"
        f"Relevant properties: {json.dumps(props, indent=2)}\n"
        f"Known liabilities: {json.dumps(liabilities, indent=2)}\n"
        f"Read-across summary: {read_across_summary or 'none'}\n"
        f"Read-across analogs: {json.dumps(read_across_analogs[:3], indent=2)}\n"
        f"Read-across endpoints: {json.dumps(read_across_endpoints[:10], indent=2)}\n"
        f"Read-across evidence: {json.dumps(read_across_evidence[:3], indent=2)}\n"
        f"Pathway review: {json.dumps(review, indent=2)}\n\n"
        "Return ONLY structured JSON matching this schema:\n"
        '{"candidates":[{"name":"...","type":"KE|AO","confidence":0.0,"reasoning":"..."}]}\n\n'
        "Use only your provided databases and skills. Do not add prose. "
        "Prefer candidates grounded in documented analogs, shared target class, shared exact mechanism, or strong structural similarity. "
        "If the pathway is shallow or generic, return more intermediate candidates and avoid final outcomes."
    )
    payload = as_dict(run_agent("aop_expert", prompt, Candidate_List))
    cands = payload.get("candidates", []) if isinstance(payload, dict) else []

    invalid_analog_candidates = any(
        isinstance(candidate, dict)
        and (
            "-like effect" in str(candidate.get("name", "")).lower()
            or "based on similarity to" in str(candidate.get("reasoning", "")).lower()
        )
        for candidate in cands
    )
    if invalid_analog_candidates:
        cands = []

    if not cands or all(_is_placeholder_candidate(c) for c in cands):
        state["candidates"] = []
        state["similarity_scores"] = []
        state["no_candidate_cycles"] = state.get("no_candidate_cycles", 0) + 1
        state["next_action"] = "expand"
        state["termination_reason"] = "AOP-Expert returned no supported downstream KE/AO candidates"
        add_provenance(state, "candidate_gen", "aop_expert", "No supported downstream KE/AO candidates returned; read-across retained as supporting evidence only", source_hint=state.get("chemical", ""), read_across_summary=read_across_summary)
        state["messages"].append({"role": "agent", "agent": "aop_expert", "content": payload})
        return state

    cands = [dict(c) for c in cands]
    for candidate in cands:
        candidate.setdefault("source", "aop_expert")
    cands.sort(key=lambda c: float(c.get("confidence") or 0.0), reverse=True)
    cands = cands[:3]

    # Print candidate information
    print(f"\n{'='*60}")
    print(f"CANDIDATE GENERATION RESULTS FOR: {chem}")
    print(f"{'='*60}")
    print(f"\nChosen candidate(s):")
    for i, cand in enumerate(cands, 1):
        print(f"  {i}. {cand.get('name', 'Unknown')}")
        print(f"     Type: {cand.get('type', 'Unknown')}")
        print(f"     Confidence: {cand.get('confidence', 0.0)}")
        print(f"     Reasoning: {cand.get('reasoning', 'No reasoning provided')}")
    
    if read_across_analogs:
        print(f"\nSimilar molecules found:")
        for i, analog in enumerate(read_across_analogs[:3], 1):
            print(f"  {i}. {analog.get('name', 'Unknown')}")
            if isinstance(analog, dict):
                similarity = analog.get('similarity', 0.0)
                if similarity:
                    print(f"     Similarity: {similarity}")
    
    state["candidates"] = cands
    state["no_candidate_cycles"] = 0
    add_provenance(
        state,
        "candidate_gen",
        "aop_expert",
        f"Generated {len(cands)} candidates",
        source_hint=state.get("chemical", ""),
        pathway_review=review,
        read_across_summary=read_across_summary,
        read_across_analogs=[a.get("name", "unknown") for a in read_across_analogs[:3] if isinstance(a, dict)],
        read_across_endpoints=read_across_endpoints[:5],
    )
    state["messages"].append({"role": "agent", "agent": "aop_expert", "content": payload})
    return state


def expand_and_prune_node(state: AOPState) -> AOPState:
    candidates = state.get("candidates", [])
    review = pathway_review(state)
    read_across = state.get("data", {}).get("read_across", {}) if isinstance(state.get("data", {}), dict) else {}
    
    # Check if candidates are just placeholders or very low confidence
    if not candidates or all(_is_placeholder_candidate(c) for c in candidates):
        state["is_ao_reached"] = False
        state["next_action"] = "candidate_gen" if state.get("no_candidate_cycles", 0) < NO_CANDIDATE_LIMIT else "terminate"
        state["termination_reason"] = state.get("termination_reason") or "No supported AOP candidates returned"
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        add_provenance(state, "expand", "aop_constructor", "No candidates available; returning to AOP-Expert for another evidence pass", pathway_review=review)
        return state
    
    # If candidates have very low confidence, try to generate better ones
    avg_confidence = sum(float(c.get("confidence", 0.0)) for c in candidates) / max(len(candidates), 1)
    if avg_confidence < 0.2:
        # Try to regenerate candidates with more specific prompting
        state["no_candidate_cycles"] = state.get("no_candidate_cycles", 0) + 1
        state["next_action"] = "candidate_gen"
        state["termination_reason"] = "Low confidence candidates generated, regenerating"
        add_provenance(state, "expand", "aop_constructor", "Low confidence candidates, regenerating", pathway_review=review, avg_confidence=avg_confidence)
        return state

    metrics = calculate_confidence_metrics(state)
    prompt = (
        f"Chemical: {state.get('chemical', '')}\n"
        f"Current pathway: {json.dumps(state.get('AOP_pathways', []), indent=2)}\n"
        f"Candidates: {json.dumps(state.get('candidates', []), indent=2)}\n"
        f"Similarity scores: {json.dumps(state.get('similarity_scores', []), indent=2)}\n"
        f"Read-across evidence: {json.dumps(read_across, indent=2)}\n"
        f"MIEs: {json.dumps(state.get('MIEs', []), indent=2)}\n"
        f"Target profile: {json.dumps(state.get('data', {}).get('target_profile', {}), indent=2)}\n"
        f"Iteration: {state.get('iteration_count', 0)}\n"
        f"Max iterations: {MAX_ITERATIONS}\n"
        f"Rejected candidates so far: {json.dumps(state.get('rejected_candidates', []), indent=2)}\n"
        f"Pathway review: {json.dumps(review, indent=2)}\n\n"
        f"Calculated quantitative metrics:\n{json.dumps(metrics, indent=2)}\n\n"
        "Return ONLY structured JSON matching this schema:\n"
        '{"selected_candidate":{"name":"...","type":"KE|AO","confidence":0.0,"similarity":0.0,"reasoning":""},"updated_pathway":[{"event":"...","type":"MIE|KE|AO","score":0.0,"provenance":[]}],"uncertainty":0.0,"decision_risk":"low|medium|high","next_action":"expand|prune|branch|terminate","is_ao_reached":false,"termination_reason":"","decision_reason":"","rejected_candidates":[]}\n\n'
        "Use the provided metrics to guide the decision, but let the orchestrator compute the final confidence locally. "
        "Prefer chemical-specific evidence, but avoid premature termination."
    )
    payload = as_dict(run_agent("aop_constructor", prompt, PathwayDecision))
    if not isinstance(payload, dict):
        raise RuntimeError(f"aop_constructor returned unexpected output: {payload}")
    decision = PathwayDecision.model_validate(payload)

    has_aop_evidence = any(
        isinstance(step, dict)
        and str(step.get("source", step.get("provenance_source", ""))).lower() == "aop_expert"
        for step in decision.updated_pathway
    ) or any(
        isinstance(candidate, dict) and str(candidate.get("source", "")).lower() == "aop_expert"
        for candidate in candidates
    )
    ao_index = next(
        (i for i, s in enumerate(decision.updated_pathway)
         if isinstance(s, dict) and str(s.get("type", "")).upper() == "AO"),
        None,
    )
    if ao_index is not None and has_aop_evidence:
        decision.updated_pathway = decision.updated_pathway[: ao_index + 1]
        decision.is_ao_reached = True
        decision.next_action = "terminate"
        decision.termination_reason = decision.termination_reason or "AO reached from AOP-Expert-supported pathway"
        
        # If we have a reasonable pathway and confidence, accept the AO
        if len(decision.updated_pathway) >= 3 and state.get("confidence_score", 0) > 0.5:
            decision.is_ao_reached = True
            decision.next_action = "terminate"
            decision.termination_reason = "AO reached with sufficient evidence"
    elif ao_index is not None:
        decision.updated_pathway = [
            step for step in decision.updated_pathway
            if not (isinstance(step, dict) and str(step.get("type", "")).upper() == "AO")
        ]
        decision.is_ao_reached = False
        decision.next_action = "expand"
        decision.termination_reason = "AO proposed without AOP-Expert-supported pathway evidence"

    if decision.is_ao_reached and not pathway_depth_ok(decision.updated_pathway):
        # Be more lenient about pathway depth when confidence is high
        confidence_score = state.get("confidence_score", 0)
        if confidence_score > 0.6 and len(decision.updated_pathway) >= 2:
            # Accept AO even if pathway is slightly short but confidence is high
            pass
        else:
            decision.is_ao_reached = False
            decision.next_action = "expand"
            decision.termination_reason = "Outcome proposed before minimum pathway depth was reached"
            decision.updated_pathway = [s for s in decision.updated_pathway if not (isinstance(s, dict) and str(s.get("type", "")).upper() == "AO")] or state.get("AOP_pathways", [])

    if decision.next_action == "terminate" and review.get("should_expand"):
        decision.next_action = "expand"
        decision.termination_reason = review.get("reason") or "Forced expansion: pathway still too shallow for termination"

    state["AOP_pathways"] = decision.updated_pathway
    current_sig = pathway_signature(state["AOP_pathways"])
    if current_sig == state.get("previous_pathway_signature", ""):
        state["no_progress_cycles"] = state.get("no_progress_cycles", 0) + 1
    else:
        state["no_progress_cycles"] = 0
        state["previous_pathway_signature"] = current_sig
    
    # Print pathway information
    print(f"\n{'='*60}")
    print(f"PATHWAY EXPANSION RESULTS FOR: {state.get('chemical', '')}")
    print(f"{'='*60}")
    print(f"\nCurrent AOP Pathway:")
    for i, step in enumerate(state["AOP_pathways"], 1):
        event_type = step.get('type', 'Unknown')
        event_desc = step.get('description', 'No description')
        event_score = step.get('score', 0.0)
        print(f"  {i}. {event_type}: {event_desc}")
        print(f"     Score: {event_score}")
        if event_type == 'MIE':
            print(f"     MIE: {step.get('event', 'Unknown')}")
    
    if decision.selected_candidate:
        print(f"\nSelected candidate for next step:")
        print(f"  Name: {decision.selected_candidate.name}")
        print(f"  Type: {decision.selected_candidate.type}")
        print(f"  Confidence: {decision.selected_candidate.confidence}")
        print(f"  Similarity: {decision.selected_candidate.similarity}")

    force_terminate = state["no_progress_cycles"] >= NO_PROGRESS_LIMIT
    if force_terminate:
        state["next_action"] = "terminate"
        state["termination_reason"] = "Pathway stopped changing"

    local_breakdown = build_local_confidence_breakdown(state, decision.updated_pathway)
    state["confidence_score"] = local_breakdown["local_confidence_score"]
    state["confidence_breakdown"] = local_breakdown
    state["uncertainty"] = float(np.clip(1.0 - state["confidence_score"], 0.0, 1.0))
    state["decision_risk"] = "low" if state["confidence_score"] >= 0.75 else ("medium" if state["confidence_score"] >= 0.5 else "high")

    if not force_terminate:
        state["next_action"] = decision.next_action if not review.get("should_expand") else "expand"
    state["decision_reason"] = decision.decision_reason or review.get("reason", "")
    state["rejected_candidates"] = decision.rejected_candidates or state.get("rejected_candidates", [])

    last_is_ao = bool(
        decision.updated_pathway
        and isinstance(decision.updated_pathway[-1], dict)
        and str(decision.updated_pathway[-1].get("type", "")).upper() == "AO"
        and has_aop_evidence
    )
    state["is_ao_reached"] = bool(decision.is_ao_reached or last_is_ao)
    if state["is_ao_reached"] and not pathway_depth_ok(state.get("AOP_pathways", [])):
        # Be more lenient about pathway depth when confidence is high
        confidence_score = state.get("confidence_score", 0)
        if confidence_score > 0.6 and len(state.get("AOP_pathways", [])) >= 2:
            # Accept AO even if pathway is slightly short but confidence is high
            pass
        else:
            state["is_ao_reached"] = False
            state["next_action"] = "expand"
            state["termination_reason"] = "Outcome rejected because minimum pathway depth was not met"
    elif not force_terminate:
        state["termination_reason"] = decision.termination_reason or review.get("reason", "") or ("Final pathway state reached" if state["is_ao_reached"] else "")

    if decision.selected_candidate:
        add_provenance(
            state,
            "expand",
            "aop_constructor",
            "AOP Constructor selected the next pathway step",
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
    state["messages"].append({"role": "agent", "agent": "aop_constructor", "content": payload})
    return state


def critic_review(state: AOPState, pathway: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    review = pathway_review(state, pathway)
    pathway = state.get("AOP_pathways", []) if pathway is None else pathway
    flags = {
        "template_overlap": float(review.get("template_overlap", 0.0)),
        "pathway_uniqueness": float(review.get("pathway_uniqueness", 0.0)),
        "generic_score": float(review.get("generic_score", 0.0)),
        "template_reuse": False,
        "premature_termination": False,
    }
    if state.get("next_action") == "terminate" and pathway:
        flags["premature_termination"] = True
    if flags["template_overlap"] >= TEMPLATE_OVERLAP_THRESHOLD and len(pathway) >= max(3, MIN_PATHWAY_LENGTH - 1):
        flags["template_reuse"] = True

    next_action = state.get("next_action", "expand")
    termination_reason = state.get("termination_reason", "")
    if not pathway:
        next_action = "expand"
        termination_reason = "No AOP pathway has been established; additional evidence generation is required."
    elif flags["premature_termination"]:
        next_action = "expand"
        termination_reason = review.get("reason") or "Critic forced expansion: pathway is not ready to terminate"
    elif flags["template_reuse"]:
        next_action = "expand"
        termination_reason = "Critic forced expansion: pathway template reuse is too high"

    return {
        "critic_flags": flags,
        "next_action": next_action,
        "termination_reason": termination_reason,
        "should_expand": review.get("should_expand", False),
        "reason": review.get("reason", ""),
    }


def critic_node(state: AOPState) -> AOPState:
    review = critic_review(state, state.get("AOP_pathways", []))
    flags = review.get("critic_flags", {}) or {}
    state["critic_flags"] = flags
    state["next_action"] = review.get("next_action", state.get("next_action", "expand"))
    state["termination_reason"] = review.get("termination_reason", state.get("termination_reason", ""))
    state["critic_reason"] = review.get("reason", "")

    # Print critic information
    print(f"\n{'='*60}")
    print(f"CRITIC REVIEW FOR: {state.get('chemical', '')}")
    print(f"{'='*60}")
    print(f"\nNext action: {state['next_action']}")
    if state["termination_reason"]:
        print(f"Termination reason: {state['termination_reason']}")
    if state["critic_reason"]:
        print(f"Critic reason: {state['critic_reason']}")
    
    if flags:
        print(f"\nCritic flags:")
        for flag, value in flags.items():
            print(f"  {flag}: {value}")

    add_provenance(
        state,
        "critic",
        "internal_critic",
        "Local verification checkpoint",
        critic_flags=state["critic_flags"],
        critic_reason=state["critic_reason"],
    )
    return state


# -------------------------
# Visualization
# ------------------------
# Removed for simplicity

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
        "no_candidate_cycles": result.get("no_candidate_cycles", 0),
        "critic_flags": result.get("critic_flags", {}),
        "critic_reason": result.get("critic_reason", ""),
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


# NOTE: build_workflow() is now implemented in orchestrator.py as AOPOrchestrator._build_graph()
# NOTE: main() is now implemented in orchestrator.py as AOPOrchestrator.run()
# NOTE: Use orchestrator.py for the main entry point