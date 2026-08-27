#!/usr/bin/env python3
"""Fast similarity scoring for the AOP workflow."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from workflow import AOPState, SIMILARITY_THRESHOLD, NO_CANDIDATE_LIMIT, add_provenance, log

ROOT = Path(".")
AGENT_PATHS = {
    "admet_mie": ROOT / ".opencode/agents/admet-mie.md",
    "aop_expert": ROOT / ".opencode/agents/aop-expert.md",
    "constructor": ROOT / ".opencode/agents/aop-constructor.md",
    "visuals_agent": ROOT / ".opencode/agents/visuals-agent.md",
}


def safe_read(path: Path) -> str:
    return path.read_text() if path.exists() else ""


AGENT_PROMPTS = {name: safe_read(path) for name, path in AGENT_PATHS.items()}

try:
    from workflow.utils import WorkflowUtils
except Exception:  # pragma: no cover
    WorkflowUtils = None  # type: ignore


STOPWORDS = {
    "a", "an", "and", "of", "the", "to", "in", "for", "with", "via", "by", "from",
    "is", "are", "be", "as", "at", "or", "this", "that", "these", "those"
}


def as_dict(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj


def run_agent(agent_name: str, prompt: str) -> Any:
    if agent_name not in AGENT_PROMPTS:
        raise ValueError(f"Unknown agent: {agent_name}")
    full_prompt = f"{AGENT_PROMPTS[agent_name]}\n\n{prompt}".strip()

    if WorkflowUtils is not None:
        method = getattr(WorkflowUtils, "run_agent", None) or getattr(WorkflowUtils, "call_agent", None)
        if method:
            return method(agent_name=agent_name, prompt=full_prompt)

    # If WorkflowUtils isn't available, use an explicit allowed model only.
    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=os.environ.get("OPENAI_MODEL", "gemma-4-31b"),
            temperature=float(os.environ.get("OPENAI_TEMPERATURE", "0.4")),
            max_tokens=int(os.environ.get("OPENAI_MAX_TOKENS", "8192")),
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=float(os.environ.get("OPENAI_TIMEOUT", "10000")),
            max_retries=3,
        )
        return llm.invoke(full_prompt)
    except Exception as e:
        raise RuntimeError(f"Agent execution failed: {e}")


def _normalize_text(value: Any) -> str:
    text = str(value or "").lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(value: Any) -> set[str]:
    return {t for t in _normalize_text(value).split() if t and t not in STOPWORDS}


def _flatten_profile(target_profile: Dict[str, Any]) -> str:
    if not isinstance(target_profile, dict):
        return ""
    parts: List[str] = []
    props = target_profile.get("properties", {}) if isinstance(target_profile.get("properties", {}), dict) else {}
    for k, v in props.items():
        parts.append(str(k))
        if isinstance(v, (list, tuple, set)):
            parts.extend(map(str, v))
        else:
            parts.append(str(v))
    liabilities = target_profile.get("liabilities", [])
    if isinstance(liabilities, list):
        parts.extend(map(str, liabilities))
    return _normalize_text(" ".join(parts))


def _read_across_terms(state: AOPState) -> set[str]:
    ra = state.get("data", {}).get("read_across", {})
    terms: set[str] = set()
    if not isinstance(ra, dict):
        return terms
    for analog in ra.get("analogs", []) if isinstance(ra.get("analogs", []), list) else []:
        if isinstance(analog, dict):
            terms |= _tokens(analog.get("name", ""))
            terms |= _tokens(analog.get("reasoning", ""))
            terms |= _tokens(analog.get("evidence", ""))
            terms |= _tokens(analog.get("match_terms", []))
    terms |= _tokens(ra.get("summary", ""))
    return terms


def _fallback_similarity_score(
    state: AOPState,
    candidate: Dict[str, Any],
    target_profile: Dict[str, Any],
    ra_terms: set[str],
) -> Tuple[float, str]:
    cand_name = str(candidate.get("name", "unknown"))
    cand_reason = str(candidate.get("reasoning", ""))
    cand_type = str(candidate.get("type", "")).upper()

    cand_text = _normalize_text(" ".join([
        cand_name,
        cand_reason,
        cand_type,
        str(candidate.get("similarity_reasoning", "")),
    ]))
    cand_tokens = _tokens(cand_text)
    profile_tokens = _tokens(_flatten_profile(target_profile))

    name_overlap = len(_tokens(cand_name) & profile_tokens)
    reason_overlap = len(_tokens(cand_reason) & profile_tokens)
    profile_overlap = len(cand_tokens & profile_tokens)
    ra_overlap = len(cand_tokens & ra_terms) if ra_terms else 0

    confidence = float(candidate.get("confidence") or 0.0)
    prior_similarity = float(candidate.get("similarity") or 0.0)

    raw = (
        0.25 * min(1.0, name_overlap / 4.0)
        + 0.20 * min(1.0, reason_overlap / 5.0)
        + 0.30 * min(1.0, profile_overlap / 8.0)
        + 0.15 * min(1.0, ra_overlap / 6.0)
        + 0.10 * max(confidence, prior_similarity)
    )
    raw = float(np.clip(raw, 0.0, 1.0))

    reasons = []
    if name_overlap:
        reasons.append("candidate name overlaps target profile")
    if reason_overlap:
        reasons.append("candidate reasoning overlaps target profile")
    if profile_overlap:
        reasons.append("candidate text overlaps target profile terms")
    if ra_overlap:
        reasons.append("supported by read-across terms")
    if confidence or prior_similarity:
        reasons.append("candidate confidence carried forward")

    return raw, "; ".join(reasons) if reasons else "Local similarity score from profile and read-across overlap"


def score_candidate(state: AOPState, candidate: Dict[str, Any], top_profile_text: str, ra_terms: set[str]) -> Dict[str, Any]:
    cand_name = candidate.get("name", "unknown")
    cand_reason = candidate.get("reasoning", "")
    cand_type = str(candidate.get("type", "")).upper()

    cand_text = _normalize_text(" ".join([cand_name, cand_reason, cand_type, str(candidate.get("similarity_reasoning", ""))]))
    cand_tokens = _tokens(cand_text)
    profile_tokens = _tokens(top_profile_text)

    name_overlap = len(_tokens(cand_name) & profile_tokens)
    reason_overlap = len(_tokens(cand_reason) & profile_tokens)
    profile_overlap = len(cand_tokens & profile_tokens)
    ra_overlap = len(cand_tokens & ra_terms) if ra_terms else 0

    confidence = float(candidate.get("confidence") or 0.0)
    prior_similarity = float(candidate.get("similarity") or 0.0)

    raw = (
        0.25 * min(1.0, name_overlap / 4.0)
        + 0.20 * min(1.0, reason_overlap / 5.0)
        + 0.30 * min(1.0, profile_overlap / 8.0)
        + 0.15 * min(1.0, ra_overlap / 6.0)
        + 0.10 * max(confidence, prior_similarity)
    )
    raw = float(np.clip(raw, 0.0, 1.0))

    reasons = []
    if name_overlap:
        reasons.append("candidate name overlaps target profile")
    if reason_overlap:
        reasons.append("candidate reasoning overlaps target profile")
    if profile_overlap:
        reasons.append("candidate text overlaps target profile terms")
    if ra_overlap:
        reasons.append("supported by read-across terms")
    if confidence or prior_similarity:
        reasons.append("candidate confidence carried forward")

    return {
        "name": cand_name,
        "similarity": raw,
        "reasoning": "; ".join(reasons) if reasons else "Local similarity score from profile and read-across overlap",
    }


def similarity_scoring_node(state: AOPState) -> AOPState:
    candidates = sorted(
        state.get("candidates", []),
        key=lambda c: float(c.get("confidence") or 0.0),
        reverse=True,
    )[:3]

    if not candidates:
        state["similarity_scores"] = []
        state["no_candidate_cycles"] = state.get("no_candidate_cycles", 0) + 1
        state["next_action"] = "terminate" if state["no_candidate_cycles"] >= NO_CANDIDATE_LIMIT else "expand"
        state["termination_reason"] = state.get("termination_reason") or "No candidates generated"
        add_provenance(state, "Similarity_Scoring", "admet_mie", "No candidates to score", no_candidates=True)
        return state

    target_profile = state.get("data", {}).get("target_profile", {})
    props = target_profile.get("properties", {}) if isinstance(target_profile, dict) else {}
    top_profile_text = _flatten_profile(target_profile)
    ra_terms = _read_across_terms(state)

    all_sims = []
    for cand in candidates:
        cand_name = cand.get("name", "unknown")
        prompt = (
            f"Chemical: {state.get('chemical', '')}\n"
            f"Candidate to score: {cand_name}\n"
            f"Candidate details: {json.dumps(cand, indent=2)}\n"
            f"Current pathway: {json.dumps(state.get('AOP_pathways', []), indent=2)}\n"
            f"MIEs: {json.dumps(state.get('MIEs', []), indent=2)}\n"
            f"Target ADMET profile: {json.dumps(target_profile, indent=2)}\n"
            f"Similarity-relevant properties: {json.dumps(props, indent=2)}\n"
            f"Similarity threshold: {SIMILARITY_THRESHOLD}\n\n"
            "Return ONLY structured JSON matching this schema:\n"
            '{"similarities":[{"name":"...","similarity":0.0,"reasoning":"..."}]}\n\n'
            "Score based on direct chemical similarity, shared target class, shared exact mechanism, shared pharmacophore, and adverse-effect profile. "
            "Prefer chemical-specific evidence."
        )

        try:
            res = as_dict(run_agent("admet_mie", prompt))
            if isinstance(res, dict) and "similarities" in res:
                sim_list = res["similarities"]
                match = next((s for s in sim_list if s.get("name") == cand_name), {})
                sim_value = float(match.get("similarity", 0.0) or 0.0)
                reasoning = str(match.get("reasoning", ""))
                if not reasoning:
                    sim_value, reasoning = _fallback_similarity_score(state, cand, target_profile, ra_terms)
                all_sims.append({"name": cand_name, "similarity": sim_value, "reasoning": reasoning})
            else:
                sim_value, reasoning = _fallback_similarity_score(state, cand, target_profile, ra_terms)
                all_sims.append({"name": cand_name, "similarity": sim_value, "reasoning": reasoning})
        except Exception as e:
            log(f"Error scoring candidate {cand_name}: {e}")
            sim_value, reasoning = _fallback_similarity_score(state, cand, target_profile, ra_terms)
            all_sims.append({"name": cand_name, "similarity": sim_value, "reasoning": f"{reasoning}; fallback used after error: {e}"})

    if not all_sims:
        state["similarity_scores"] = []
        state["no_candidate_cycles"] = state.get("no_candidate_cycles", 0) + 1
        state["next_action"] = "terminate"
        state["termination_reason"] = state.get("termination_reason") or "No candidates scored"
        add_provenance(state, "Similarity_Scoring", "admet_mie", "No candidate similarities returned", no_candidates=True)
        return state

    smap = {s.get("name"): s for s in all_sims if isinstance(s, dict) and s.get("name")}
    state["similarity_scores"] = all_sims

    # Print similarity scoring information
    print(f"\n{'='*60}")
    print(f"SIMILARITY SCORING RESULTS FOR: {state.get('chemical', '')}")
    print(f"{'='*60}")
    print(f"\nSimilarity scores for candidates:")
    for sim in all_sims:
        print(f"  {sim.get('name', 'Unknown')}: {sim.get('similarity', 0.0)}")
        print(f"     Reasoning: {sim.get('reasoning', 'No reasoning provided')}")
    
    updated = []
    for c in candidates:
        item = dict(c)
        s = smap.get(item.get("name"))
        if s:
            item["similarity"] = s.get("similarity")
            item["similarity_reasoning"] = s.get("reasoning", "")
        updated.append(item)

    # Don't filter on early iterations when building the pathway
    iteration_count = state.get("iteration_count", 0)
    pathway_length = len(state.get("AOP_pathways", []))
    
    # Only apply similarity filtering after we have some pathway progress
    if iteration_count > 1 and pathway_length > 0:
        filtered = [c for c in updated if float(c.get("similarity") or 0.0) >= SIMILARITY_THRESHOLD]
    else:
        # On early iterations, keep all candidates regardless of similarity score
        filtered = updated

    state["candidates"] = sorted(
        filtered,
        key=lambda c: float(c.get("similarity") or c.get("confidence") or 0.0),
        reverse=True,
    )[:3]

    if not state["candidates"]:
        state["no_candidate_cycles"] = state.get("no_candidate_cycles", 0) + 1
        state["next_action"] = "terminate" if state["no_candidate_cycles"] >= NO_CANDIDATE_LIMIT else "expand"
        state["termination_reason"] = state.get("termination_reason") or "No candidates met similarity threshold"
    else:
        state["no_candidate_cycles"] = 0

    add_provenance(state, "Similarity_Scoring", "admet_mie", f"Scored {len(all_sims)} candidates")
    state.setdefault("messages", []).append({"role": "agent", "agent": "admet_mie", "content": {"similarities": all_sims}})
    return state


__all__ = ["similarity_scoring_node", "score_candidate", "run_agent"]