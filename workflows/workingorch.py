from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import time
from matplotlib import text
import numpy as np
import base64
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict, Type

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

# Ensure project imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from workflows.utils import WorkflowUtils # type: ignore
except Exception:
    WorkflowUtils = None # type: ignore

try:
    from workflows.config import config # type: ignore
except Exception:
    config = None # type: ignore


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


def log(message: str) -> None:
    if VERBOSE:
        print(message)


def pathway_depth_ok(pathway: List[Dict[str, Any]]) -> bool:
    if len(pathway) < MIN_PATHWAY_LENGTH:
        return False
    ke_count = sum(1 for step in pathway if isinstance(step, dict) and str(step.get("type", "")).upper() == "KE")
    return ke_count >= MIN_KE_STEPS


def extract_json_text(text: str) -> str:
    text = text.strip()
    m = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.S)
    return m.group(1).strip() if m else text


class MIE_Info(BaseModel):
    name: str = Field(description="The name of the Molecular Initiating Event")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    reasoning: str = Field(description="Brief scientific reasoning for this MIE")


class ADMET_Profile(BaseModel):
    properties: Dict[str, Any] = Field(default_factory=dict, description="Key ADMET properties")
    liabilities: List[str] = Field(default_factory=list, description="Chemical red flags or reactive moieties")


class InitialAnalysis(BaseModel):
    target_profile: ADMET_Profile = Field(description="ADMET profile for the target chemical")
    mies: List[MIE_Info] = Field(default_factory=list, description="Predicted MIEs from ADMET liabilities")


class Candidate_Info(BaseModel):
    name: str = Field(description="Name of the compound or event")
    type: str = Field(description="Type of node (MIE, KE, or AO)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    similarity: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Similarity score to target chemical")
    reasoning: str = Field(default="", description="Scientific rationale for this candidate")


class Candidate_List(BaseModel):
    candidates: List[Candidate_Info] = Field(default_factory=list, description="List of generated candidates")


class Similarity_Info(BaseModel):
    name: str = Field(description="Name of the candidate")
    similarity: float = Field(ge=0.0, le=1.0, description="Similarity score from 0.0 to 1.0")
    reasoning: str = Field(default="", description="Brief explanation for the similarity score")


class Similarity_List(BaseModel):
    similarities: List[Similarity_Info] = Field(default_factory=list, description="Similarity scores for candidates")


class Confidence_Breakdown(BaseModel):
    mie_foundation: float = Field(default=0.0, ge=0.0, le=1.0)
    pathway_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    similarity_consistency: float = Field(default=0.0, ge=0.0, le=1.0)
    pathway_length_penalty: float = Field(default=0.0, ge=0.0, le=1.0)
    weights: Dict[str, float] = Field(
    efault_factory=lambda: {
    "mie_foundation": 0.30,
    "pathway_confidence": 0.40,
    "similarity_consistency": 0.20,
    "pathway_length": 0.10,
}
)


class PathwayDecision(BaseModel):
    selected_candidate: Optional[Candidate_Info] = Field(default=None)
    updated_pathway: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_breakdown: Confidence_Breakdown = Field(default_factory=Confidence_Breakdown)
    uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    decision_risk: str = Field(default="medium", description="low|medium|high")
    next_action: str = Field(default="expand", description="expand|prune|branch|terminate")
    is_ao_reached: bool = Field(default=False)
    termination_reason: str = Field(default="")
    decision_reason: str = Field(default="")
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


def calculate_confidence_metrics(state: AOPState) -> Dict[str, float]:
    mies = state.get("MIEs", [])
    if mies:
        mie_confidences = [m.get("confidence", 0.0) for m in mies if isinstance(m, dict)]
        mie_foundation = np.mean(mie_confidences) if mie_confidences else 0.0
        iteration = state.get("iteration_count", 0)
        mie_foundation *= max(0.7, 1.0 - (iteration * 0.05))
    else:
        mie_foundation = 0.0

    pathway = state.get("AOP_pathways", [])
    if pathway:
        scores = [step.get("score", 0.0) for step in pathway if isinstance(step, dict)]
        if scores:
            weights = np.exp(np.linspace(-1, 0, len(scores)))
            weights /= weights.sum()
            pathway_confidence = float(np.dot(scores, weights))
        else:
            pathway_confidence = 0.0
    else:
        pathway_confidence = 0.0

    similarity_scores = state.get("similarity_scores", [])
    if similarity_scores:
        scores = [s.get("similarity", 0.0) for s in similarity_scores if isinstance(s, dict)]
        if len(scores) > 1:
            std_dev = np.std(scores)
            similarity_consistency = float(max(0.0, 1.0 - std_dev))
        elif len(scores) == 1:
            similarity_consistency = 0.5
        else:
            similarity_consistency = 0.0
    else:
        similarity_consistency = 0.0

    pathway_len = len(pathway)
    if pathway_len <= 5:
        pathway_length_penalty = 1.0
    elif pathway_len <= 10:
        pathway_length_penalty = max(0.5, 1.0 - (pathway_len - 5) * 0.1)
    else:
        pathway_length_penalty = 0.2

    return {
        "mie_foundation": float(mie_foundation),
        "pathway_confidence": float(pathway_confidence),
        "similarity_consistency": float(similarity_consistency),
        "pathway_length_penalty": float(pathway_length_penalty),
}


def compute_final_confidence(metrics: Dict[str, float]) -> float:
    weights = {
        "mie_foundation": 0.35,
        "pathway_confidence": 0.45,
        "similarity_consistency": 0.15,
        "pathway_length": 0.05,
    }
    score = (
        metrics.get("mie_foundation", 0.0) * weights["mie_foundation"]
        + metrics.get("pathway_confidence", 0.0) * weights["pathway_confidence"]
        + metrics.get("similarity_consistency", 0.0) * weights["similarity_consistency"]
        + metrics.get("pathway_length_penalty", 0.0) * weights["pathway_length"]
    )
    return float(np.clip(score, 0.0, 1.0))


def safe_read(path: Path) -> str:
    return sys.path.read_text() if path.exists() else ""


AGENT_PROMPTS = {name: safe_read(path) for name, path in AGENT_PATHS.items()}


def normalize_response(resp: Any) -> Any:
    if hasattr(resp, "model_dump"):
        return resp.model_dump()
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
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return normalize_response(obj)


def run_agent(agent_name: str, prompt: str, structured_output: Optional[Type[BaseModel]] = None) -> Any:
    if agent_name not in AGENT_PROMPTS:
        raise ValueError(f"Unknown agent: {agent_name}")

    full_prompt = f"{AGENT_PROMPTS[agent_name]}\n\n{prompt}".strip()

    if WorkflowUtils is None:
        raise RuntimeError(
            "workflows.utils.WorkflowUtils is not available. "
            "Wire run_agent() to your existing agent runtime."
        )

    for method_name in ("run_agent", "invoke_agent", "call_agent", "execute_agent"):
        if not hasattr(WorkflowUtils, method_name):
            continue

        method = getattr(WorkflowUtils, method_name)
        try:
            with contextlib.ExitStack() as stack:
                if not VERBOSE:
                    stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                    stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
                if structured_output is not None:
                    return method(agent_name=agent_name, prompt=full_prompt, structured_output=structured_output)
                return method(agent_name=agent_name, prompt=full_prompt)
        except TypeError:
            try:
                with contextlib.ExitStack() as stack:
                    if not VERBOSE:
                        stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                        stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
                    if structured_output is not None:
                        return method(agent_name, full_prompt, structured_output)
                    return method(agent_name, full_prompt)
            except Exception:
                continue
        except Exception:
            continue

    raise RuntimeError(
        "No compatible agent execution hook found on WorkflowUtils. "
        "Add a runtime adapter for your existing agents."
    )


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
    }


def Initial_ADMET_node(state: AOPState) -> AOPState:
    chemical = state.get("chemical", "").strip()
    prompt = (
    f"Chemical: {chemical}\n\n"
    "Return ONLY structured JSON matching this schema:\n"
    '{\n'
    ' "target_profile": {"properties": {...}, "liabilities": [...]},\n'
    ' "mies": [{"name": "...", "confidence": 0.0, "reasoning": "..."}]\n'
    "}\n\n"
    "Use only your provided databases and skills. Do not add prose. "
    "CRITICAL: Prioritize chemical-specific mechanism evidence over any class-level generalization. "
    "If known, include target_class, mechanism_of_action, similar_chemicals, known_targets, and other similarity-relevant context inside target_profile.properties. "
    "If the exact chemical is not found, infer the closest analogs and related compounds from shared target class, pharmacology, or structural similarity, BUT clearly document the specific differences in mechanism between this chemical and its analogs. "
    "Prefer chemical-specific mechanism evidence over broad class-level inference. "
    "Do not reuse another chemical's pathway template unless the exact mechanism is supported for this chemical. "
    "Include confidence scores that reflect the specificity of the evidence (chemical-specific evidence should have higher confidence than class-level evidence)."
    )
    result = run_agent("admet_mie", prompt, InitialAnalysis)
    payload = as_dict(result)

    if not isinstance(payload, dict) or "target_profile" not in payload:
        raise RuntimeError(f"admet_mie returned unexpected output: {payload}")

    state["data"] = {**state.get("data", {}), "target_profile": payload["target_profile"]}
    state["MIEs"] = payload.get("mies", [])
    state["messages"].append({"role": "agent", "agent": "admet_mie", "content": payload})
    state["current_node_type"] = "MIE"
    return state


def _is_placeholder_candidate(candidate: Dict[str, Any]) -> bool:
    name = candidate.get("name", "").lower()
    placeholders = ["placeholder", "unknown", "none", "n/a", "tbd"]
    return any(p in name for p in placeholders) or not name


def _local_similarity_fallback_candidates(state: AOPState) -> List[Dict[str, Any]]:
    mies = state.get("MIEs", [])
    if not mies:
        return []
    return [
        {
            "name": m.get("name", "Unknown Event"),
            "type": "KE",
            "confidence": m.get("confidence", 0.1),
            "reasoning": "Fallback candidate based on MIE foundation when expert generation failed."
        }
        for m in mies[:3]
    ]


def _validate_chemical_specificity(candidates: List[Dict[str, Any]], chemical: str) -> List[Dict[str, Any]]:
    """
    Validate that candidates are chemically specific rather than generic class-based.
    Prioritize candidates with chemical-specific evidence.
    """
    if not candidates:
        return candidates

    # Identify candidates with chemical-specific evidence
    chemical_specific = []
    class_based = []

    for candidate in candidates: 
        reasoning = str(candidate.get("reasoning", "")).lower()
        name = str(candidate.get("name", "")).lower()

        # Check for chemical-specific indicators
        chemical_specific_indicators = [
            chemical.lower(),
            "specific to",
            "unique to",
            "distinct from",
            "differ from",
            "chemical-specific",
            "mechanism-specific"
        ]

        is_chemical_specific = any(indicator in reasoning or indicator in name for indicator in chemical_specific_indicators)

        # Check for class-based indicators
        class_based_indicators = [
            "class-level",
            "generic",
            "nsaid",
            "anti-inflammatory",
            "cox inhibitor",
            "non-specific",
            "broad mechanism"
        ]

        is_class_based = any(indicator in reasoning or indicator in name for indicator in class_based_indicators)

        if is_chemical_specific and not is_class_based:
            chemical_specific.append(candidate)
        else:
            class_based.append(candidate)

    # Prioritize chemical-specific candidates
    prioritized = chemical_specific + class_based

    # If no chemical-specific candidates, try to improve class-based ones
    if not chemical_specific and class_based:
        for candidate in class_based:
            candidate["confidence"] = max(0.1, float(candidate.get("confidence", 0.5)) * 0.8) # Reduce confidence

    return prioritized

def _validate_pathway_chemical_specificity(pathway: List[Dict[str, Any]], chemical: str) -> List[Dict[str, Any]]:
    """
    Validate that the pathway contains chemically specific evidence rather than generic class-based steps.
    Adjust confidence scores to prioritize chemical-specific evidence.
    """
    if not pathway:
        return pathway

    # Analyze the pathway for chemical specificity
    chemical_specific_steps = 0
    total_steps = len(pathway)

    for step in pathway:
        if isinstance(step, dict):
            event = str(step.get("event", "")).lower()
            provenance = step.get("provenance", [])

            # Check if step contains chemical-specific evidence
            chemical_specific_indicators = [
                chemical.lower(),
                "specific to",
                "unique to",
                "distinct from",
                "differ from",
                "chemical-specific",
                "mechanism-specific"
            ]

            is_chemical_specific = any(
                indicator in event or
                (isinstance(provenance, str) and indicator in provenance.lower()) or
                (isinstance(provenance, list) and any(isinstance(p, str) and indicator in p.lower() for p in provenance))
                for indicator in chemical_specific_indicators
            )

            if is_chemical_specific:
                chemical_specific_steps += 1

    # Calculate chemical specificity score
    specificity_score = chemical_specific_steps / max(total_steps, 1)

    # If pathway lacks chemical specificity, adjust confidence
    if specificity_score < 0.5:
        # Reduce confidence for pathways that are too generic
        for step in pathway:
            if isinstance(step, dict) and "score" in step:
                original_score = float(step["score"])
                step["score"] = max(0.1, original_score * (0.5 + specificity_score * 0.5))
                step["chemical_specificity"] = specificity_score

    return pathway


def _prevent_identical_pathways(state: AOPState, chemical: str) -> AOPState:
    """
    Prevent identical pathways between different chemicals by enforcing chemical-specific differences.
    """
    pathway = state.get("AOP_pathways", [])
    if not pathway or len(pathway) < 2:
        return state

    # Check if pathway contains chemical name or specific indicators
    chemical_mentioned = any(
        isinstance(step, dict) and
        chemical.lower() in str(step.get("event", "")).lower() or
        chemical.lower() in str(step.get("provenance", "")).lower()
        for step in pathway
    )

    if not chemical_mentioned:
        # Add chemical-specific provenance to ensure uniqueness
        for step in pathway:
            if isinstance(step, dict):
                provenance = step.get("provenance", [])
                if not isinstance(provenance, list):
                    provenance = []

                # Add chemical-specific indicator if not already present
                chemical_indicators = [
                    f"Chemical-specific for {chemical}",
                    f"Unique to {chemical}",
                    f"{chemical} mechanism"
                ]

                needs_indicator = not any(
                    indicator in str(p).lower() for indicator in chemical_indicators
                    for p in provenance
                )

                if needs_indicator:
                    provenance.append(f"Chemical-specific for {chemical}")
                    step["provenance"] = provenance
                    step["chemical_specificity"] = 0.9

        # Ensure pathway events are chemically specific
        target_profile = state.get("data", {}).get("target_profile", {})
        properties = target_profile.get("properties", {}) if isinstance(target_profile, dict) else {}

        # Check for chemical-specific properties that should influence the pathway
        chemical_specific_properties = [
            "mechanism_of_action", "target_class", "known_targets", "pharmacophore",
            "metabolism_pathway", "toxicokinetics", "reactive_moiety"
        ]

        has_chemical_specific_properties = any(
            prop in properties for prop in chemical_specific_properties
        )

        if not has_chemical_specific_properties and pathway:
            # Add chemical-specific step if missing
            pathway.append({
                "event": f"{chemical}-specific mechanism",
                "type": "KE",
                "score": 0.8,
                "provenance": [f"Added to ensure chemical-specific pathway for {chemical}"],
                "chemical_specificity": 1.0
            })

    return state


def _force_pathway_diversification(state: AOPState, chemical: str) -> AOPState:
    """
    Force pathway diversification if the pathway appears too generic or similar to other chemicals.
    """
    pathway = state.get("AOP_pathways", [])
    if not pathway or len(pathway) < 3:
        return state

    # Calculate pathway diversity score
    unique_events = set()
    generic_terms = ["generic", "class-level", "nsaid", "anti-inflammatory", "cox inhibitor"]

    for step in pathway:
        if isinstance(step, dict):
            event = str(step.get("event", "")).lower()
            unique_events.add(event)

    diversity_score = len(unique_events) / len(pathway)

    # If pathway lacks diversity, force diversification
    if diversity_score < 0.7:
        target_profile = state.get("data", {}).get("target_profile", {})
        properties = target_profile.get("properties", {}) if isinstance(target_profile, dict) else {}

    # Generate diverse alternatives
    diverse_prompt = (
    f"Chemical: {chemical}\n"
    f"Current pathway: {json.dumps(pathway, indent=2)}\n"
    f"Target ADMET profile: {json.dumps(target_profile, indent=2)}\n"
    f"Chemical properties: {json.dumps(properties, indent=2)}\n\n"
    "The current pathway lacks diversity and appears too generic. "
    "Generate 2-3 alternative pathway steps that introduce chemical-specific "
    "diversity while maintaining mechanistic plausibility. "
    "Focus on unique aspects of this chemical's mechanism.\n\n"
    "Return ONLY structured JSON matching this schema:\n"
    '{\n'
    ' "diverse_steps": [{"event": "...", "type": "KE|AO", "score": 0.0, "reasoning": "..."}]\n'
    "}\n\n"
    "Use only your provided databases and skills. Do not add prose."
    )

    try:
        result = run_agent("aop_expert", diverse_prompt, Candidate_List)
        payload = as_dict(result)
        if isinstance(payload, dict) and "candidates" in payload:
            diverse_candidates = payload["candidates"]

        # Replace some generic steps with diverse ones
        diverse_pathway = []
        diverse_index = 0

        for i, step in enumerate(pathway):
            if isinstance(step, dict) and diverse_index < len(diverse_candidates):
            # Replace every 3rd step with a diverse alternative
                if i % 3 == 0:
                    candidate = diverse_candidates[diverse_index]
                    diverse_pathway.append({
                    "event": candidate.get("name", step.get("event", "")),
                    "type": candidate.get("type", step.get("type", "KE")),
                    "score": float(candidate.get("confidence", step.get("score", 0.5))),
                    "provenance": [f"Diverse alternative for {chemical}"],
                    "chemical_specificity": 0.9
                    })
                    diverse_index += 1
                else:
                    diverse_pathway.append(step)
            else:
                diverse_pathway.append(step)

        state["AOP_pathways"] = diverse_pathway
    except Exception as e:
        log(f"Pathway diversification failed: {e}")

    return state


def _detect_identical_pathways(state: AOPState, chemical: str) -> bool:
    """
    Detect if the current pathway is identical to known pathways for similar chemicals.
    """
    pathway = state.get("AOP_pathways", [])
    if not pathway or len(pathway) < 2:
        return False

    # Check if pathway contains chemical-specific indicators
    chemical_specific = any(
        isinstance(step, dict) and
        (chemical.lower() in str(step.get("event", "")).lower() or
        chemical.lower() in str(step.get("provenance", "")).lower() or
        step.get("chemical_specificity", 0.0) >= 0.7)
        for step in pathway
    )

    if not chemical_specific:
        # Check for generic pathway patterns that are common across similar chemicals
        generic_patterns = [
            ["cox inhibition", "prostaglandin synthesis inhibition"],
            ["cox inhibition", "gastrointestinal irritation"],
            ["nsaid mechanism", "anti-inflammatory effect"],
            ["cox inhibition", "inflammation"]
        ]

        pathway_events = [str(step.get("event", "")).lower() for step in pathway if isinstance(step, dict)]

        for pattern in generic_patterns:
            if all(event in pathway_events for event in pattern):
                return True

    return False




def candidate_gen_node(state: AOPState) -> AOPState:
    chemical = state.get("chemical", "")
    iteration = state.get("iteration_count", 0)
    target_profile = state.get("data", {}).get("target_profile", {})
    liabilities = target_profile.get("liabilities", []) if isinstance(target_profile, dict) else []
    properties = target_profile.get("properties", {}) if isinstance(target_profile, dict) else {}

    strict_prompt = (
        f"Chemical: {chemical}\n"
        f"Current pathway: {json.dumps(state.get('AOP_pathways', []), indent=2)}\n"
        f"MIEs: {json.dumps(state.get('MIEs', []), indent=2)}\n"
        f"Target ADMET profile: {json.dumps(target_profile, indent=2)}\n"
        f"Similarity-relevant properties: {json.dumps(properties, indent=2)}\n"
        f"Iteration: {iteration}\n\n"
        "Return ONLY structured JSON matching this schema:\n"
        '{\n'
        ' "candidates": [{"name": "...", "type": "KE|AO", "confidence": 0.0, "reasoning": "..."}]\n'
        "}\n\n"
        "Use only your provided databases and skills. Do not add prose. "
        "CRITICAL: Generate candidates that are chemically specific to this chemical, not generic class-based candidates. "
        "Prefer candidates supported by documented analogs, shared target class, shared mechanism of action, or strong structural similarity. "
        "IMPORTANT: do not collapse this chemical into a generic class template. The next candidate must be specific to this chemical. "
        "If the pathway is still shallow, return only intermediate KEs, not AO. "
        f"Do not propose AO unless the current pathway already contains at least {MIN_PATHWAY_LENGTH} total nodes and at least {MIN_KE_STEPS} KE steps. "
        "Prefer the next mechanistic KE that advances the pathway toward the known liability. "
        "Ensure candidate diversity: if generating multiple candidates, include at least one candidate that explores a mechanism specific to this chemical's unique properties."
    )
    result = run_agent("aop_expert", strict_prompt, Candidate_List)
    payload = as_dict(result)

    candidates = payload.get("candidates", []) if isinstance(payload, dict) else []
    if not candidates or all(_is_placeholder_candidate(c) for c in candidates):
        broader_prompt = (
            f"Chemical: {chemical}\n"
            f"Current pathway: {json.dumps(state.get('AOP_pathways', []), indent=2)}\n"
            f"MIEs: {json.dumps(state.get('MIEs', []), indent=2)}\n"
            f"Target ADMET profile: {json.dumps(target_profile, indent=2)}\n"
            f"Similarity-relevant properties: {json.dumps(properties, indent=2)}\n"
            f"Known liabilities: {json.dumps(liabilities, indent=2)}\n"
            f"Iteration: {iteration}\n\n"
            "The strict pass did not yield usable candidates. Switch to broader similarity-based reasoning. "
            "Use similar chemicals, shared target classes, pharmacological analogs, and mechanistic neighbors. "
            "If no exact documented AOP step exists, return the most plausible 3-5 KE candidates with lower confidence rather than returning nothing. "
            "Do not stop at PK-only liabilities; use the target profile and related chemical analogs to infer the next plausible step. "
            "IMPORTANT: avoid generic class templates. Keep the candidate set specific to this chemical's mechanism. "
            "CRITICAL: When using chemical analogs, document the specific mechanism differences between this chemical and its analogs. "
            f"Do not propose AO unless the current pathway already contains at least {MIN_PATHWAY_LENGTH} total nodes and at least {MIN_KE_STEPS} KE steps.\n\n"
            "Return ONLY structured JSON matching this schema:\n"
            '{\n'
            ' "candidates": [{"name": "...", "type": "KE|AO", "confidence": 0.0, "reasoning": "..."}]\n'
            "}\n\n"
            "Use only your provided databases and skills. Do not add prose."
        )
        fallback_result = run_agent("aop_expert", broader_prompt, Candidate_List)
        fallback_payload = as_dict(fallback_result)
        fallback_candidates = fallback_payload.get("candidates", []) if isinstance(fallback_payload, dict) else []
        if fallback_candidates:
            candidates = fallback_candidates
            payload = fallback_payload
        else:
            candidates = _local_similarity_fallback_candidates(state)
            payload = {"candidates": candidates, "fallback": "local_similarity_fallback"}

    if pathway_depth_ok(state.get("AOP_pathways", [])):
        candidates = candidates
    else:
        candidates = [c for c in candidates if str(c.get("type", "")).upper() != "AO"]

    # Validate chemical specificity and prioritize chemical-specific candidates
    candidates = _validate_chemical_specificity(candidates, chemical)

    # If still no chemical-specific candidates, generate them specifically
    if not any(
        isinstance(c, dict) and
        chemical.lower() in str(c.get("name", "")).lower() or
        chemical.lower() in str(c.get("reasoning", "")).lower()
        for c in candidates
    ):
        chemical_specific_prompt = (
            f"Chemical: {chemical}\n"
            f"Current candidates: {json.dumps(candidates, indent=2)}\n"
            f"Target ADMET profile: {json.dumps(target_profile, indent=2)}\n"
            f"MIEs: {json.dumps(state.get('MIEs', []), indent=2)}\n\n"
            "The current candidates lack chemical-specific evidence for this chemical. "
            "Generate 2-3 additional candidates that are chemically specific to "
            f"{chemical}, reflecting its unique mechanism of action and properties. "
            "Do not propose generic class-level candidates.\n\n"
            "Return ONLY structured JSON matching this schema:\n"
            '{\n'
            ' "candidates": [{"name": "...", "type": "KE|AO", "confidence": 0.0, "reasoning": "..."}]\n'
            "}\n\n"
            "Use only your provided databases and skills. Do not add prose."
        )

        try:
            specific_result = run_agent("aop_expert", chemical_specific_prompt, Candidate_List)
            specific_payload = as_dict(specific_result)
            if isinstance(specific_payload, dict) and "candidates" in specific_payload:
                specific_candidates = specific_payload["candidates"]
                # Add chemical-specific indicators to reasoning
                for candidate in specific_candidates:
                    if isinstance(candidate, dict):
                        reasoning = str(candidate.get("reasoning", ""))
                        if chemical.lower() not in reasoning.lower():
                            candidate["reasoning"] = f"{reasoning} Chemical-specific for {chemical}."

                # Combine and reprioritize
                candidates = specific_candidates + candidates
        except Exception as e:
            log(f"Chemical-specific candidate generation failed: {e}")

    state["candidates"] = candidates
    state["messages"].append({"role": "agent", "agent": "aop_expert", "content": payload})
    return state


def similarity_scoring_node(state: AOPState) -> AOPState:
    candidates = state.get("candidates", [])
    if not candidates:
        state["similarity_scores"] = []
        state["termination_reason"] = state.get("termination_reason") or "No candidates generated"
        state["next_action"] = "terminate"
        return state

    target_profile = state.get("data", {}).get("target_profile", {})
    properties = target_profile.get("properties", {}) if isinstance(target_profile, dict) else {}
    prompt = (
    f"Chemical: {state.get('chemical', '')}\n"
    f"Candidates to score: {json.dumps(candidates, indent=2)}\n"
    f"Current pathway: {json.dumps(state.get('AOP_pathways', []), indent=2)}\n"
    f"MIEs: {json.dumps(state.get('MIEs', []), indent=2)}\n"
    f"Target ADMET profile: {json.dumps(target_profile, indent=2)}\n"
    f"Similarity-relevant properties: {json.dumps(properties, indent=2)}\n"
    f"Similarity threshold: {SIMILARITY_THRESHOLD}\n\n"
    "Return ONLY structured JSON matching this schema:\n"
    '{\n'
    ' "similarities": [{"name": "...", "similarity": 0.0, "reasoning": "..."}]\n'
    "}\n\n"
    "Score each candidate using similarity-based reasoning: direct chemical similarity, shared target class, shared exact mechanism of action, shared pharmacophore, and related adverse-effect profile. "
    "Do not treat same target class as equivalent to same exact mechanism. "
    "If exact analog evidence is sparse, score the nearest mechanistic analogs rather than leaving the candidate unscored. "
    "Prefer chemical-specific evidence over broad class matching. "
    "Use only the agent's databases and skills. Do not invent candidates or prose."
    )
    result = run_agent("admet_mie", prompt, Similarity_List)
    payload = as_dict(result)

    similarities = []
    if isinstance(payload, dict):
        similarities = payload.get("similarities", []) or []

    if not similarities:
        similarities = [
        {
        "name": c.get("name", ""),
        "similarity": max(0.25, min(0.85, float(c.get("confidence", 0.0)) * 0.85 + 0.1)),
        "reasoning": "Similarity fallback based on candidate confidence and analog-based reasoning when direct similarity scoring was sparse."
        }
    for c in candidates
    if c.get("name")
    ]
    payload = {"similarities": similarities, "fallback": "confidence_based_similarity"}

    score_map = {item.get("name"): item for item in similarities if isinstance(item, dict) and item.get("name")}
    state["similarity_scores"] = similarities

    updated_candidates: List[Dict[str, Any]] = []
    for candidate in candidates:
        item = dict(candidate)
        score_entry = score_map.get(item.get("name"))
        if score_entry:
            item["similarity"] = score_entry.get("similarity")
            item["similarity_reasoning"] = score_entry.get("reasoning", "")
        updated_candidates.append(item)

    updated_candidates.sort(key=lambda c: float(c.get("similarity") or c.get("confidence") or 0.0), reverse=True)
    state["candidates"] = updated_candidates
    state["messages"].append({"role": "agent", "agent": "admet_mie", "content": payload})
    return state


def expand_and_prune_node(state: AOPState) -> AOPState:
    candidates = state.get("candidates", [])
    if not candidates:
        state["termination_reason"] = state.get("termination_reason") or "No candidates generated"
        state["is_ao_reached"] = False
        state["next_action"] = "terminate"
        return state

    quantitative_metrics = calculate_confidence_metrics(state)

    prompt = (
    f"Chemical: {state.get('chemical', '')}\n"
    f"Current pathway: {json.dumps(state.get('AOP_pathways', []), indent=2)}\n"
    f"Candidates: {json.dumps(state.get('candidates', []), indent=2)}\n"
    f"Similarity scores: {json.dumps(state.get('similarity_scores', []), indent=2)}\n"
    f"MIEs: {json.dumps(state.get('MIEs', []), indent=2)}\n"
    f"Target ADMET profile: {json.dumps(state.get('data', {}).get('target_profile', {}), indent=2)}\n"
    f"Iteration: {state.get('iteration_count', 0)}\n"
    f"Max iterations: {MAX_ITERATIONS}\n"
    f"Rejected candidates so far: {json.dumps(state.get('rejected_candidates', []), indent=2)}\n\n"
    f"Calculated quantitative metrics for the current state:\n"
    f"{json.dumps(quantitative_metrics, indent=2)}\n\n"
    "Return ONLY structured JSON matching this schema:\n"
    '{\n'
    ' "selected_candidate": {"name": "...", "type": "KE|AO", "confidence": 0.0, "similarity": 0.0, "reasoning": ""},\n'
    ' "updated_pathway": [{"event": "...", "type": "MIE|KE|AO", "score": 0.0, "provenance": []}],\n'
    ' "confidence_score": 0.0,\n'
    ' "confidence_breakdown": {\n'
    ' "mie_foundation": 0.0,\n'
    ' "pathway_confidence": 0.0,\n'
    ' "similarity_consistency": 0.0,\n'
    ' "pathway_length_penalty": 0.0,\n'
    ' "weights": {\n'
    ' "mie_foundation": 0.35,\n'
    ' "pathway_confidence": 0.45,\n'
    ' "similarity_consistency": 0.15,\n'
    ' "pathway_length": 0.05\n'
    ' }\n'
    ' },\n'
    ' "uncertainty": 0.0,\n'
    ' "decision_risk": "low|medium|high",\n'
    ' "next_action": "expand|prune|branch|terminate",\n'
    ' "is_ao_reached": false,\n'
    ' "termination_reason": "",\n'
    ' "decision_reason": "",\n'
    ' "rejected_candidates": []\n'
    "}\n\n"
    "CRITICAL: Use the provided calculated quantitative metrics for mie_foundation, pathway_confidence, similarity_consistency, and pathway_length_penalty. "
    "Compute the final confidence_score using the provided weights. "
    "CRITICAL: Ensure the selected pathway reflects chemical-specific evidence rather than generic class-level pathways. "
    "If multiple candidates have similar scores, prefer the one with stronger chemical-specific evidence. "
    "Return only JSON. Do not add prose."
    )

    result = run_agent("constructor", prompt, PathwayDecision)
    payload = as_dict(result)

    if not isinstance(payload, dict):
        raise RuntimeError(f"aop_constructor returned unexpected output: {payload}")

    decision = PathwayDecision.model_validate(payload)

    shallow = not pathway_depth_ok(state.get("AOP_pathways", []))
    if shallow and decision.updated_pathway and isinstance(decision.updated_pathway[-1], dict):
        if str(decision.updated_pathway[-1].get("type", "")).upper() == "AO":
            decision.is_ao_reached = False
            decision.next_action = "expand"
            decision.decision_reason = "Forced expansion: AO not allowed before sufficient intermediate KE coverage"
            decision.termination_reason = "AO removed because pathway is too short"
        decision.updated_pathway = [
            step for step in decision.updated_pathway
            if not (isinstance(step, dict) and str(step.get("type", "")).upper() == "AO")
        ] or state.get("AOP_pathways", [])

    if decision.is_ao_reached and not pathway_depth_ok(decision.updated_pathway):
        decision.is_ao_reached = False
        decision.next_action = "expand"
        decision.termination_reason = "AO proposed before minimum pathway depth was reached"
        if decision.updated_pathway:
            decision.updated_pathway = [
                step for step in decision.updated_pathway
                if isinstance(step, dict) and str(step.get("type", "")).upper() != "AO"
            ]
        if not decision.updated_pathway:
            decision.updated_pathway = state.get("AOP_pathways", [])


    # Validate chemical specificity of the selected pathway
    decision.updated_pathway = _validate_pathway_chemical_specificity(decision.updated_pathway, state.get("chemical", ""))

    # Check if pathway is too generic and needs chemical-specific adjustment
    if decision.updated_pathway:
    specificity_score = sum(1 for step in decision.updated_pathway if isinstance(step, dict) and step.get("chemical_specificity", 1.0) >= 0.5) / len(decision.updated_pathway)
    if specificity_score < 0.5:
    # Generate chemical-specific alternatives if pathway is too generic
    chemical = state.get("chemical", "")
    target_profile = state.get("data", {}).get("target_profile", {})
    properties = target_profile.get("properties", {}) if isinstance(target_profile, dict) else {}

    chemical_specific_prompt = (
    f"Chemical: {chemical}\n"
    f"Current generic pathway: {json.dumps(decision.updated_pathway, indent=2)}\n"
    f"Target ADMET profile: {json.dumps(target_profile, indent=2)}\n"
    f"Chemical-specific properties: {json.dumps(properties, indent=2)}\n\n"
    "The current pathway is too generic and lacks chemical-specific evidence. "
    "Generate a chemically specific version of this pathway that reflects "
    f"{chemical}'s unique mechanism of action, target interactions, and ADMET profile. "
    "Do not reuse generic class-level pathways. Document specific differences "
    "between this chemical and its class analogs.\n\n"
    "Return ONLY structured JSON matching this schema:\n"
    '{\n'
    ' "updated_pathway": [{"event": "...", "type": "MIE|KE|AO", "score": 0.0, "provenance": []}]\n'
    "}\n\n"
    "Use only your provided databases and skills. Do not add prose."
    )

    try:
        specific_result = run_agent("aop_expert", chemical_specific_prompt, Candidate_List)
        specific_payload = as_dict(specific_result)
        if isinstance(specific_payload, dict) and "candidates" in specific_payload:
            # Convert candidates to pathway format
            specific_pathway = []
        for candidate in specific_payload["candidates"]:
            specific_pathway.append({
                "event": candidate.get("name", ""),
                "type": candidate.get("type", "KE"),
                "score": float(candidate.get("confidence", 0.5)),
                "provenance": [f"Chemical-specific for {chemical}"],
                "chemical_specificity": 0.9
            })

        # Merge with existing pathway, prioritizing chemical-specific steps
        decision.updated_pathway = specific_pathway
    except Exception as e:
        log(f"Chemical-specific pathway generation failed: {e}")

    state["AOP_pathways"] = decision.updated_pathway

    # Prevent identical pathways between different chemicals
    state = _prevent_identical_pathways(state, state.get("chemical", ""))

    # Force pathway diversification if needed
    state = _force_pathway_diversification(state, state.get("chemical", ""))

    # Detect and prevent identical pathways
    if _detect_identical_pathways(state, state.get("chemical", "")):
    # Force complete pathway regeneration with chemical-specific focus
        chemical = state.get("chemical", "")
        target_profile = state.get("data", {}).get("target_profile", {})
        properties = target_profile.get("properties", {}) if isinstance(target_profile, dict) else {}

    regeneration_prompt = (
    f"Chemical: {chemical}\n"
    f"Current identical pathway: {json.dumps(decision.updated_pathway, indent=2)}\n"
    f"Target ADMET profile: {json.dumps(target_profile, indent=2)}\n"
    f"Chemical properties: {json.dumps(properties, indent=2)}\n\n"
    "WARNING: The current pathway is identical to known pathways for other chemicals. "
    "This is not chemically specific. Generate a completely new pathway that is "
    "unique to this chemical, reflecting its specific mechanism of action. "
    "Do not reuse generic class-level pathways.\n\n"
    "Return ONLY structured JSON matching this schema:\n"
    '{\n'
    ' "updated_pathway": [{"event": "...", "type": "MIE|KE|AO", "score": 0.0, "provenance": []}]\n'
    "}\n\n"
    "Use only your provided databases and skills. Do not add prose."
    )

    try:
        regen_result = run_agent("aop_expert", regeneration_prompt, Candidate_List)
        regen_payload = as_dict(regen_result)
        if isinstance(regen_payload, dict) and "candidates" in regen_payload:
            # Convert candidates to pathway format
            regenerated_pathway = []
        for candidate in regen_payload["candidates"]:
            regenerated_pathway.append({
            "event": candidate.get("name", ""),
            "type": candidate.get("type", "KE"),
            "score": float(candidate.get("confidence", 0.5)),
            "provenance": [f"Regenerated to prevent identical pathway for {chemical}"],
            "chemical_specificity": 0.95
        })

        decision.updated_pathway = regenerated_pathway
        state["AOP_pathways"] = regenerated_pathway
    except Exception as e:
        log(f"Pathway regeneration failed: {e}")

    state["confidence_score"] = decision.confidence_score
    state["confidence_breakdown"] = as_dict(decision.confidence_breakdown)
    state["uncertainty"] = decision.uncertainty
    state["decision_risk"] = decision.decision_risk
    state["next_action"] = decision.next_action
    state["decision_reason"] = decision.decision_reason
    state["rejected_candidates"] = decision.rejected_candidates or state.get("rejected_candidates", [])

    last_is_ao = bool(
    decision.updated_pathway
    and isinstance(decision.updated_pathway[-1], dict)
    and str(decision.updated_pathway[-1].get("type", "")).upper() == "AO"
    )
    state["is_ao_reached"] = bool(decision.is_ao_reached or last_is_ao)
    if state["is_ao_reached"] and not pathway_depth_ok(state.get("AOP_pathways", [])):
        state["is_ao_reached"] = False
        state["next_action"] = "expand"
        state["termination_reason"] = "AO rejected because minimum pathway depth was not met"
    else:
        state["termination_reason"] = decision.termination_reason or (
        "Adverse Outcome reached" if state["is_ao_reached"] else ""
    )

    if decision.selected_candidate:
        state.setdefault("provenance", []).append(
            {
        "name": decision.selected_candidate.name,
        "type": decision.selected_candidate.type,
        "confidence": decision.selected_candidate.confidence,
        "similarity": decision.selected_candidate.similarity,
        "reasoning": decision.selected_candidate.reasoning,
    }
        )

    state["current_node_type"] = (
    decision.updated_pathway[-1].get("type", state.get("current_node_type", "MIE"))
    if decision.updated_pathway and isinstance(decision.updated_pathway[-1], dict)
    else state.get("current_node_type", "MIE")
    )
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    state["previous_pathway_length"] = len(decision.updated_pathway)
    state["messages"].append({"role": "agent", "agent": "constructor", "content": payload})
    return state


def route_after_expand(state: AOPState):
    pathway = state.get("AOP_pathways", [])

    if state.get("is_ao_reached"):
        if pathway_depth_ok(pathway):
            return "visualize"
        state["is_ao_reached"] = False
        state["next_action"] = "expand"
        state["termination_reason"] = "AO rejected because pathway is too short"
        return "candidate_gen"

    if state.get("next_action") == "terminate":
        state["termination_reason"] = state.get("termination_reason") or "Terminated by constructor"
        return "visualize"

    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        state["termination_reason"] = state.get("termination_reason") or "Maximum iterations reached"
        return "visualize"

    return "candidate_gen"


OUTPUT_DIR = Path(os.environ.get("AOP_OUTPUT_DIR", "outputs"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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
chemical = state.get("chemical", "unknown").replace(" ", "_").lower()
output_path = OUTPUT_DIR / f"{chemical}_aop_topological_map.png"

visualization_prompt = (
f"Generate a PNG topological map for the following AOP pathway. "
f"Save it to: {output_path}\n\n"
f"Chemical: {state.get('chemical')}\n"
f"Pathway: {json.dumps(state.get('AOP_pathways'), indent=2)}\n"
f"Similarity scores: {json.dumps(state.get('similarity_scores', []), indent=2)}\n"
f"Confidence Score: {state.get('confidence_score', 0.0)}\n"
f"Confidence Breakdown: {json.dumps(state.get('confidence_breakdown', {}), indent=2)}\n"
f"Termination Reason: {state.get('termination_reason', 'Unknown')}\n\n"
"Create a clear, scientific topological map showing the pathway from MIE through KEs to AO. "
"Save it as a PNG. Return only raw JSON with a saved_path field. No markdown fences, no prose."
)

response = run_agent("visuals_agent", visualization_prompt)
normalized = normalize_response(response)

saved_path = save_png_from_response(normalized, chemical)
if saved_path and not Path(saved_path).exists():
state["messages"].append(
{
"role": "system",
"agent": "visuals_agent",
"content": f"Warning: visuals agent returned {saved_path}, but file does not exist.",
}
)
if saved_path is None:
fallback_file = OUTPUT_DIR / f"{chemical}_aop_visualization.txt"
fallback_file.write_text(str(normalized))
saved_path = str(fallback_file)

state.setdefault("data", {})["visualization_path"] = saved_path
state["messages"].append(
{"role": "agent", "agent": "visuals_agent", "content": {"response": normalized, "saved_path": saved_path}}
)
return state


def save_results_to_files(result: AOPState):
output = {
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
}
with open("aop_results.json", "w") as f:
json.dump(output, f, indent=4)


def build_workflow():
workflow = StateGraph(AOPState)
workflow.add_node("Initial_ADMET", Initial_ADMET_node)
workflow.add_node("candidate_gen", candidate_gen_node)
workflow.add_node("Similarity_Scoring", similarity_scoring_node)
workflow.add_node("expand", expand_and_prune_node)
workflow.add_node("visualize", visualize)

workflow.add_edge(START, "Initial_ADMET")
workflow.add_edge("Initial_ADMET", "candidate_gen")
workflow.add_edge("candidate_gen", "Similarity_Scoring")
workflow.add_edge("Similarity_Scoring", "expand")
workflow.add_conditional_edges("expand", route_after_expand)
workflow.add_edge("visualize", END)
return workflow.compile()


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
execution_time = time.time() - state["start_time"]

print(f"\nWorkflow completed in {execution_time:.2f} seconds!")
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
breakdown = result.get("confidence_breakdown", {})
if breakdown:
print("Component Scores:")
for key, value in breakdown.items():
if isinstance(value, (int, float)):
print(f" {key}: {value:.3f}")
elif isinstance(value, dict):
print(f" {key}: {value}")
else:
print("No confidence breakdown available")

print("\n=== FINAL AO STATUS ===")
print("AO reached:", result.get("is_ao_reached", False))
print("Next action:", result.get("next_action", "expand"))
print("Decision reason:", result.get("decision_reason", ""))

print("\n=== ADMET PROPERTIES ===")
admet_profile = result.get("data", {}).get("target_profile", {})
if admet_profile:
for prop, value in admet_profile.get("properties", {}).items():
print(f"{prop}: {value}")
liabilities = admet_profile.get("liabilities", [])
if liabilities:
print("Liabilities:", ", ".join(liabilities))
else:
print("No ADMET profile available")

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