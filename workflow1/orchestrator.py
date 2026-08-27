from __future__ import annotations

import json
import os
import time
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from langgraph.graph import END, START, StateGraph

from workflow import (
    AOPState,
    Initial_ADMET_node,
    PathwayDecision,
    add_provenance,
    as_dict,
    build_local_confidence_breakdown,
    candidate_gen_node,
    critic_node,
    expand_and_prune_node,
    initial_state,
    log,
    run_agent,
)
from read_across import enrich_read_across_state
from similarity_scoring import similarity_scoring_node

# Finalization / AO routing heuristics
# More lenient values to allow AO closure when evidence supports it
READ_ACROSS_FINALIZE_CONFIDENCE = float(os.environ.get("AOP_READ_ACROSS_FINALIZE_CONFIDENCE", "0.25"))
READ_ACROSS_FINALIZE_MIN_ANALOGS = int(os.environ.get("AOP_READ_ACROSS_FINALIZE_MIN_ANALOGS", "1"))
READ_ACROSS_FINALIZE_MIN_TOP_SIM = float(os.environ.get("AOP_READ_ACROSS_FINALIZE_MIN_TOP_SIM", "0.40"))
AOP_FORCE_FINALIZE_MIN_CONFIDENCE = float(os.environ.get("AOP_FORCE_FINALIZE_MIN_CONFIDENCE", "0.50"))
AOP_FORCE_FINALIZE_MIN_PATHWAY_LENGTH = int(os.environ.get("AOP_FORCE_FINALIZE_MIN_PATHWAY_LENGTH", "2"))

#Tracking for workflow execution times and success rates
class WorkflowMonitor:
    """Basic monitoring for workflow execution"""

    def __init__(self):
        self.metrics = {
            'node_execution_times': {},
            'node_success_rates': {},
            'total_start_time': None,
            'total_end_time': None,
            'node_call_counts': {}
        }
        self.reset_metrics()

    def reset_metrics(self):
        """Reset metrics for a new workflow run"""
        self.metrics['node_execution_times'] = {}
        self.metrics['node_success_rates'] = {}
        self.metrics['node_call_counts'] = {}
        self.metrics['total_start_time'] = time.time()

    def track_node_execution(self, node_name: str, execution_time: float, success: bool):
        """Track node performance metrics"""
        current_time = self.metrics['node_execution_times'].get(node_name, 0)
        count = self.metrics['node_call_counts'].get(node_name, 0) + 1
        self.metrics['node_execution_times'][node_name] = (
            current_time + execution_time
        ) / count

        self.metrics['node_call_counts'][node_name] = count

        success_count = self.metrics['node_success_rates'].get(node_name, {}).get('success', 0)
        if success:
            success_count += 1
        self.metrics['node_success_rates'][node_name] = {
            'success': success_count,
            'total': count,
            'rate': success_count / count if count > 0 else 0
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get current monitoring metrics"""
        self.metrics['total_end_time'] = time.time()
        self.metrics['total_execution_time'] = (
            self.metrics['total_end_time'] - self.metrics['total_start_time']
        )
        return self.metrics

    def print_summary(self):
        """Print monitoring summary"""
        metrics = self.get_metrics()
        print("\n" + "="*60)
        print("WORKFLOW MONITORING SUMMARY")
        print("="*60)
        print(f"Total Execution Time: {metrics['total_execution_time']:.2f} seconds")
        print(f"\nNode Performance:")
        for node_name in sorted(metrics['node_execution_times'].keys()):
            exec_time = metrics['node_execution_times'][node_name]
            call_count = metrics['node_call_counts'][node_name]
            print(f"  {node_name:20s} | Time: {exec_time:.3f}s | Calls: {call_count}")
        print("="*60 + "\n")


def parallel_candidate_generation(state: AOPState) -> AOPState:
    return candidate_gen_node(state)

# Run read across and store information
def enrich_read_across_node(state: AOPState) -> AOPState:
    chemical = str(state.get("chemical", "")).strip()
    data = state.setdefault("data", {}) if isinstance(state.get("data", {}), dict) else {}

    # Make sure read_across has the ADMET profile it expects.
    if "target_profile" in data and "admet_profile" not in data:
        data["admet_profile"] = data.get("target_profile", {})

    # Run read-across only once per workflow run.
    if data.get("read_across_attempted"):
        log(f"Read-across already attempted for {chemical}, reusing cached result")
        return state

    data["read_across_attempted"] = True

    # If a valid result already exists, keep it.
    cached_ra = data.get("read_across", {})
    if isinstance(cached_ra, dict) and cached_ra:
        log(f"Read-across already computed for {chemical}, skipping calculation")
        return state

    source = os.environ.get("TOX21_DB_FILE", "tox21_database.csv")
    if not os.path.exists(source):
        source = None

    use_ctx = os.environ.get("USE_CTX_PYTHON", "false").lower() == "true"

    # Ensure we have the necessary data before running read-across
    if not chemical:
        log(f"Cannot run read-across: no chemical name provided")
        return state
    
    if "target_profile" not in data:
        log(f"Cannot run read-across: no target_profile available for {chemical}")
        return state

    enrich_read_across_state(
        state,
        reference_source=source,
        use_ctx=use_ctx,
    )
    return state


def _read_across_summary(state: AOPState) -> Dict[str, Any]:
    ra = state.get("data", {}).get("read_across", {}) if isinstance(state.get("data", {}), dict) else {}
    if not isinstance(ra, dict):
        ra = {}
    analogs = ra.get("analogs", []) if isinstance(ra.get("analogs", []), list) else []
    conf = float(ra.get("confidence") or 0.0)
    top_sim = 0.0
    avg_sim = 0.0
    if analogs:
        sims = []
        for a in analogs:
            if isinstance(a, dict):
                sims.append(float(a.get("similarity") or a.get("score") or 0.0))
        if sims:
            top_sim = max(sims)
            avg_sim = sum(sims) / len(sims)
    return {
        "raw": ra,
        "analog_count": len(analogs),
        "confidence": conf,
        "top_similarity": top_sim,
        "avg_similarity": avg_sim,
        "summary": str(ra.get("summary", "")),
        "analogs": analogs,
    }


def _should_attempt_finalize(state: AOPState) -> bool:
    ra = _read_across_summary(state)
    pathway_length = len(state.get("AOP_pathways", []))
    confidence_score = float(state.get("confidence_score", 0.0) or 0.0)
    
    # More lenient conditions for finalization
    # Allow finalization if we have either:
    # 1. Strong read-across evidence AND sufficient pathway length, OR
    # 2. High confidence score AND reasonable pathway length
    
    has_read_across_evidence = ra["analog_count"] >= max(1, READ_ACROSS_FINALIZE_MIN_ANALOGS // 2)
    has_good_similarity = ra["top_similarity"] >= max(0.3, READ_ACROSS_FINALIZE_MIN_TOP_SIM * 0.6)
    has_sufficient_pathway = pathway_length >= max(2, AOP_FORCE_FINALIZE_MIN_PATHWAY_LENGTH // 2)
    has_high_confidence = confidence_score >= max(0.5, AOP_FORCE_FINALIZE_MIN_CONFIDENCE * 0.7)
    
    # Attempt finalization if:
    # - We have read-across evidence AND sufficient pathway length, OR
    # - We have high confidence AND reasonable pathway length
    condition1 = (has_read_across_evidence and has_good_similarity and has_sufficient_pathway)
    condition2 = (has_high_confidence and has_sufficient_pathway)
    
    return condition1 or condition2

# Last chance to finalize the pathway to an AO if evidence is strong
def finalize_aop_node(state: AOPState) -> AOPState:
    """Give the constructor one final chance to close the pathway to an AO when evidence is strong."""
    if state.get("is_ao_reached"):
        return state
    if not _should_attempt_finalize(state):
        return state

    ra = _read_across_summary(state)
    target_profile = state.get("data", {}).get("target_profile", {}) if isinstance(state.get("data", {}), dict) else {}
    prompt = (
        f"Chemical: {state.get('chemical', '')}\n"
        f"Current pathway: {json.dumps(state.get('AOP_pathways', []), indent=2)}\n"
        f"Current candidates: {json.dumps(state.get('candidates', []), indent=2)}\n"
        f"Similarity scores: {json.dumps(state.get('similarity_scores', []), indent=2)}\n"
        f"Read-across summary: {ra.get('summary', '')}\n"
        f"Read-across analogs: {json.dumps(ra.get('analogs', [])[:5], indent=2)}\n"
        f"Target profile: {json.dumps(target_profile, indent=2)}\n\n"
        "You are the aop-constructor agent. The workflow already has strong ADMET and read-across support.\n"
        "If the evidence supports a terminal adverse outcome, return a complete pathway ending in AO.\n"
        "Do not invent unsupported steps, but DO allow a shorter scientifically supported pathway when the evidence is strong.\n"
        "Return ONLY structured JSON matching this schema:\n"
        '{"selected_candidate":{"name":"...","type":"KE|AO","confidence":0.0,"similarity":0.0,"reasoning":""},'
        '"updated_pathway":[{"event":"...","type":"MIE|KE|AO","score":0.0,"provenance":[]}],'
        '"uncertainty":0.0,"decision_risk":"low|medium|high","next_action":"expand|prune|branch|terminate",'
        '"is_ao_reached":false,"termination_reason":"","decision_reason":"","rejected_candidates":[] }\n'
        "Favor a direct closure to the adverse outcome if the pathway already contains the necessary key events.\n"
        "IMPORTANT: Be aggressive in closing pathways to AO when the evidence is strong. If the pathway contains sufficient key events and the read-across evidence supports it, add the AO step."
    )

    try:
        payload = as_dict(run_agent("aop_constructor", prompt, PathwayDecision))
        if not isinstance(payload, dict):
            return state
        decision = PathwayDecision.model_validate(payload)
    except Exception as e:
        log(f"finalize_aop_node failed: {e}")
        return state

    updated_pathway = decision.updated_pathway or state.get("AOP_pathways", [])
    if not isinstance(updated_pathway, list):
        updated_pathway = state.get("AOP_pathways", [])

    last_is_ao = bool(
        updated_pathway
        and isinstance(updated_pathway[-1], dict)
        and str(updated_pathway[-1].get("type", "")).upper() == "AO"
    )
    has_aop_evidence = any(
        isinstance(step, dict)
        and str(step.get("source", step.get("provenance_source", ""))).lower() == "aop_expert"
        for step in updated_pathway
    ) or any(
        isinstance(candidate, dict) and str(candidate.get("source", "")).lower() == "aop_expert"
        for candidate in state.get("candidates", [])
    )
    decision_is_ao = bool((decision.is_ao_reached or last_is_ao) and has_aop_evidence)

    if decision_is_ao:
        state["AOP_pathways"] = updated_pathway
        state["is_ao_reached"] = True
        state["next_action"] = "terminate"
        state["termination_reason"] = decision.termination_reason or "AO reached from strong ADMET + read-across evidence"
        state["decision_reason"] = decision.decision_reason or state.get("decision_reason", "")
        state["rejected_candidates"] = decision.rejected_candidates or state.get("rejected_candidates", [])
        state["current_node_type"] = (
            updated_pathway[-1].get("type", state.get("current_node_type", "MIE"))
            if updated_pathway and isinstance(updated_pathway[-1], dict)
            else state.get("current_node_type", "MIE")
        )
        local_breakdown = build_local_confidence_breakdown(state, updated_pathway)
        state["confidence_score"] = max(float(state.get("confidence_score", 0.0) or 0.0), float(local_breakdown["local_confidence_score"]))
        state["confidence_breakdown"] = local_breakdown
        state["uncertainty"] = float(max(0.0, min(1.0, 1.0 - state["confidence_score"])))
        state["decision_risk"] = "low" if state["confidence_score"] >= 0.75 else ("medium" if state["confidence_score"] >= 0.5 else "high")
        state.setdefault("messages", []).append({"role": "agent", "agent": "aop_constructor", "content": payload})
        add_provenance(
            state,
            "finalize",
            "aop_constructor",
            "Final AO closure accepted",
            confidence=decision.selected_candidate.confidence if decision.selected_candidate else None,
            similarity=decision.selected_candidate.similarity if decision.selected_candidate else None,
            selected_candidate=decision.selected_candidate.model_dump() if decision.selected_candidate else None,
            read_across_confidence=ra.get("confidence", 0.0),
            read_across_analogs=[a.get("name", "unknown") for a in ra.get("analogs", [])[:5] if isinstance(a, dict)],
        )
    return state

# Loops unless AO is reached or termination conditions are met
def adaptive_route_after_finalize(state: AOPState):
    if state.get("is_ao_reached") or state.get("next_action") == "terminate":
        return END
    if state.get("no_candidate_cycles", 0) >= int(os.environ.get("AOP_NO_CANDIDATE_LIMIT", "2")):
        return END
    if state.get("no_progress_cycles", 0) >= int(os.environ.get("AOP_NO_PROGRESS_LIMIT", "2")):
        return END
    if state.get("iteration_count", 0) >= int(os.environ.get("AOP_MAX_ITERATIONS", "10")):
        return END
    return "candidate_gen"

#Routes workflow after critic node based on confidence, pathway length, and iteration count
def adaptive_route_after_critic(state: AOPState):
    pathway = state.get("AOP_pathways", [])
    confidence = state.get("confidence_score", 0)
    iteration_count = state.get("iteration_count", 0)
    pathway_length = len(pathway)
    finalize_ready = _should_attempt_finalize(state)

    if state.get("is_ao_reached"):
        return END
    if not pathway:
        return "candidate_gen"
    if finalize_ready:
        return "finalize"
    if state.get("next_action") == "terminate":
        return END
    if state.get("no_candidate_cycles", 0) >= int(os.environ.get("AOP_NO_CANDIDATE_LIMIT", "2")):
        state["termination_reason"] = state.get("termination_reason") or "No candidates generated after fallback"
        return END
    if state.get("no_progress_cycles", 0) >= int(os.environ.get("AOP_NO_PROGRESS_LIMIT", "2")):
        state["termination_reason"] = state.get("termination_reason") or "No meaningful pathway progress"
        return END
    if iteration_count >= int(os.environ.get("AOP_MAX_ITERATIONS", "10")):
        state["termination_reason"] = state.get("termination_reason") or "Maximum iterations reached"
        return END

    # More aggressive routing to finalize when we have reasonable evidence
    if confidence > 0.6 and pathway_length >= 3:
        return "finalize"
    elif confidence > 0.5 and pathway_length >= 2 and iteration_count >= 2:
        return "finalize"
    elif confidence < 0.5 and iteration_count > 3:
        return "candidate_gen"
    elif pathway_length < 3 and iteration_count < 2:
        return "candidate_gen"
    else:
        return "candidate_gen"

# Builds and runs the AOP workflow, optionally with monitoring
class AOPOrchestrator:
    def __init__(self, enable_monitoring: bool = True):
        self.enable_monitoring = enable_monitoring
        self.monitor = WorkflowMonitor() if enable_monitoring else None
        self.graph = self._build_graph()

    def _build_graph(self):
        w = StateGraph(AOPState)

        if self.enable_monitoring:
            w.add_node("Initial_ADMET", self._monitored_node(Initial_ADMET_node, "Initial_ADMET"))
            w.add_node("read_across", self._monitored_node(enrich_read_across_node, "read_across"))
            w.add_node("candidate_gen", self._monitored_node(parallel_candidate_generation, "candidate_gen"))
            w.add_node("Similarity_Scoring", self._monitored_node(similarity_scoring_node, "Similarity_Scoring"))
            w.add_node("expand", self._monitored_node(expand_and_prune_node, "expand"))
            w.add_node("critic", self._monitored_node(critic_node, "critic"))
            w.add_node("finalize", self._monitored_node(finalize_aop_node, "finalize"))
        else:
            w.add_node("Initial_ADMET", Initial_ADMET_node)
            w.add_node("read_across", enrich_read_across_node)
            w.add_node("candidate_gen", parallel_candidate_generation)
            w.add_node("Similarity_Scoring", similarity_scoring_node)
            w.add_node("expand", expand_and_prune_node)
            w.add_node("critic", critic_node)
            w.add_node("finalize", finalize_aop_node)

        w.add_edge(START, "Initial_ADMET")
        w.add_edge("Initial_ADMET", "read_across")
        w.add_edge("read_across", "candidate_gen")
        w.add_edge("candidate_gen", "Similarity_Scoring")
        w.add_edge("Similarity_Scoring", "expand")
        w.add_edge("expand", "critic")
        w.add_conditional_edges("critic", adaptive_route_after_critic)
        w.add_conditional_edges("finalize", adaptive_route_after_finalize)
        return w.compile()

    def _monitored_node(self, node_func, node_name: str):
        def wrapper(state: AOPState) -> AOPState:
            start_time = time.time()
            try:
                result = node_func(state)
                execution_time = time.time() - start_time
                
                # Ensure minimum measurable time (1ms) for very fast nodes
                execution_time = max(execution_time, 0.001)
                
                if self.monitor:
                    self.monitor.track_node_execution(node_name, execution_time, True)
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                execution_time = max(execution_time, 0.001)
                if self.monitor:
                    self.monitor.track_node_execution(node_name, execution_time, False)
                raise e
        return wrapper

    def _print_results_summary(self, result: Dict[str, Any]):
        print("\n" + "="*60)
        print("AOP WORKFLOW RESULTS SUMMARY")
        print("="*60)
        print(f"Chemical: {result.get('chemical', 'Unknown')}")
        print(f"Adverse Outcome Reached: {result.get('is_ao_reached', False)}")
        print(f"Confidence Score: {result.get('confidence_score', 0.0):.3f}")
        print(f"Uncertainty: {result.get('uncertainty', 0.0):.3f}")
        print(f"Decision Risk: {result.get('decision_risk', 'medium').upper()}")
        print(f"Termination Reason: {result.get('termination_reason', 'Unknown')}")
        print(f"Iteration Count: {result.get('iteration_count', 0)}")

        pathway = result.get('AOP_pathways', [])
        print(f"\nPathway Length: {len(pathway)}")

        if pathway:
            print("\nPathway Steps:")
            for i, step in enumerate(pathway, 1):
                event_type = step.get('type', 'Unknown')
                event_name = step.get('event', step.get('name', 'Unknown'))
                print(f"  {i}. {event_type}: {event_name}")

        print("="*60 + "\n")

    def run(self, chemical: str) -> Dict[str, Any]:
        if self.enable_monitoring and self.monitor:
            self.monitor.reset_metrics()

        state = initial_state()
        state["chemical"] = chemical.strip()
        result = self.graph.invoke(state)

        from workflow import save_results_to_files
        save_results_to_files(result)

        self._print_results_summary(result)

        if self.enable_monitoring and self.monitor:
            self.monitor.print_summary()

        return result

# File runs the orchestrator if executed directly
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        chemical = input("Enter the chemical name: ").strip()
        if not chemical:
            print("Error: Chemical name cannot be empty")
            sys.exit(1)
    else:
        chemical = sys.argv[1]

    orchestrator = AOPOrchestrator()
    try:
        result = orchestrator.run(chemical)
        print(f"Workflow completed for {chemical}")
    except Exception as e:
        print(f"Error during workflow execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
