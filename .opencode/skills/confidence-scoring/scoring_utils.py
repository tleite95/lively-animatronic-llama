import numpy as np
from typing import List, Dict, Any

def calculate_confidence_metrics(state: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculates the quantitative components of the confidence score based on the current AOP state.
    
    Args:
        state: The current AOPState from the orchestrator.
        
    Returns:
        A dictionary containing the calculated metrics for the confidence breakdown.
    """
    # 1) MIE Foundation: Average confidence of current MIEs
    mies = state.get("MIEs", [])
    if mies:
        mie_confidences = [m.get("confidence", 0.0) for m in mies if isinstance(m, dict)]
        mie_foundation = np.mean(mie_confidences) if mie_confidences else 0.0
        # Slight reduction as iteration count increases (as per skill guidance)
        iteration = state.get("iteration_count", 0)
        mie_foundation *= max(0.7, 1.0 - (iteration * 0.05))
    else:
        mie_foundation = 0.0

    # 2) Pathway Confidence: Weighted average of pathway step scores with exponential decay
    pathway = state.get("AOP_pathways", [])
    if pathway:
        scores = [step.get("score", 0.0) for step in pathway if isinstance(step, dict)]
        if scores:
            # Exponential decay: more recent steps matter more
            weights = np.exp(np.linspace(-1, 0, len(scores)))
            weights /= weights.sum()
            pathway_confidence = float(np.dot(scores, weights))
        else:
            pathway_confidence = 0.0
    else:
        pathway_confidence = 0.0

    # 3) Similarity Consistency: Inverse of standard deviation of candidate similarity scores
    similarity_scores = state.get("similarity_scores", [])
    if similarity_scores:
        scores = [s.get("similarity", 0.0) for s in similarity_scores if isinstance(s, dict)]
        if len(scores) > 1:
            std_dev = np.std(scores)
            # Convert lower spread (std_dev) into higher consistency
            similarity_consistency = float(max(0.0, 1.0 - std_dev))
        elif len(scores) == 1:
            similarity_consistency = 0.5 # Default for single candidate
        else:
            similarity_consistency = 0.0
    else:
        similarity_consistency = 0.0

    # 4) Pathway Length Penalty: Penalty for overly long pathways
    # Assume optimal length is around 3-5 steps
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
        "pathway_length_penalty": float(pathway_length_penalty)
    }

def compute_final_confidence(metrics: Dict[str, float], reasoning_quality: float) -> float:
    """
    Computes the final confidence score using the weighted formula.
    """
    weights = {
        "mie_foundation": 0.30,
        "pathway_confidence": 0.40,
        "similarity_consistency": 0.15,
        "reasoning_quality": 0.10,
        "pathway_length": 0.05
    }
    
    score = (
        metrics.get("mie_foundation", 0.0) * weights["mie_foundation"] +
        metrics.get("pathway_confidence", 0.0) * weights["pathway_confidence"] +
        metrics.get("similarity_consistency", 0.0) * weights["similarity_consistency"] +
        reasoning_quality * weights["reasoning_quality"] +
        metrics.get("pathway_length_penalty", 0.0) * weights["pathway_length"]
    )
    
    return float(np.clip(score, 0.0, 1.0))
