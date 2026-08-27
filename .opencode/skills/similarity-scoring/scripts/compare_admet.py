import numpy as np
import json
import argparse
from typing import Dict, List, Any


def calculate_weighted_cosine_similarity(v1: np.ndarray, v2: np.ndarray, weights: np.ndarray) -> float:
    """
    Calculates the weighted cosine similarity between two vectors.
    
    Args:
        v1: First vector (target profile values).
        v2: Second vector (candidate profile values).
        weights: Weight vector for each element in the vectors.
    
    Returns:
        Weighted cosine similarity score between 0.0 and 1.0.
    """
    # Apply weights to vectors
    wv1 = v1 * weights
    wv2 = v2 * weights
    
    # Calculate norms of weighted vectors
    norm1 = np.linalg.norm(wv1)
    norm2 = np.linalg.norm(wv2)
    
    # Handle division by zero
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    # Return weighted cosine similarity
    return np.dot(wv1, wv2) / (norm1 * norm2)

def compare_admet_profiles(target_profile: Dict[str, float], candidates: List[Dict[str, Any]], weights_dict: Dict[str, float] = None) -> List[Dict[str, Any]]:
    """
    Compares a target ADMET profile against a list of candidate profiles with optional weighting.
    
    Args:
        target_profile: Dictionary of ADMET property names and values for the target compound.
        candidates: List of dictionaries, each containing a 'profile' key with ADMET values and optional 'id'/'name'/'smiles' keys.
        weights_dict: Optional dictionary mapping ADMET property names to weights for weighted similarity calculation.
    
    Returns:
        List of results sorted by similarity score (descending), where each result contains:
        - id: Candidate identifier
        - similarity: Weighted cosine similarity score (0.0 to 1.0)
        - top_divergence: Top 3 ADMET endpoints with highest absolute difference
        - common_endpoints_count: Number of overlapping ADMET endpoints
        - note: Optional note about comparison issues
    """
    results = []
    
    # Iterate through each candidate profile
    for cand in candidates:
        cand_profile = cand['profile']
        
        # Find common ADMET endpoints between target and candidate
        common_keys = sorted(list(set(target_profile.keys()) & set(cand_profile.keys())))
        
        # Handle case where no common endpoints exist
        if not common_keys:
            results.append({
                "id": cand.get("id") or cand.get("name") or cand.get("smiles"),
                "similarity": 0.0,
                "top_divergence": [],
                "note": "No overlapping ADMET endpoints"
            })
            continue
            
        # Create vectors from common ADMET endpoints
        try:
            target_vec = np.array([float(target_profile[k]) for k in common_keys])
            cand_vec = np.array([float(cand_profile[k]) for k in common_keys])
        except (ValueError, TypeError) as e:
            results.append({
                "id": cand.get("id") or cand.get("name") or cand.get("smiles"),
                "similarity": 0.0,
                "top_divergence": [],
                "note": f"Non-numeric value encountered: {str(e)}"
            })
            continue
        
        # Create weight vector for the common keys
        if weights_dict:
            # Apply custom weights if provided
            weights_vec = np.array([weights_dict.get(k, 1.0) for k in common_keys])
            similarity = calculate_weighted_cosine_similarity(target_vec, cand_vec, weights_vec)
        else:
            # Fallback to standard cosine similarity (all weights = 1.0)
            weights_vec = np.ones(len(common_keys))
            similarity = calculate_weighted_cosine_similarity(target_vec, cand_vec, weights_vec)
        
        # Calculate absolute differences for each common endpoint
        # Normalization: Divide difference by the sum of values to make it relative
        diffs = {}
        for k in common_keys:
            val1 = target_profile[k]
            val2 = cand_profile[k]
            abs_diff = abs(val1 - val2)
            # Simple relative difference to handle scale variation
            denom = (abs(val1) + abs(val2))
            diffs[k] = abs_diff / denom if denom != 0 else 0.0
        
        # Identify top 3 endpoints with highest divergence
        top_divergence = sorted(diffs.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Store results for this candidate
        results.append({
            "id": cand.get("id") or cand.get("name") or cand.get("smiles"),
            "similarity": float(similarity),
            "top_divergence": top_divergence,
            "common_endpoints_count": len(common_keys)
        })
    
    # Return results sorted by similarity score (highest first)
    return sorted(results, key=lambda x: x["similarity"], reverse=True)

def main():
    """
    Main function to handle command-line arguments and execute the ADMET comparison.
    
    This function:
    1. Parses command-line arguments
    2. Loads weight configuration
    3. Loads target and candidate ADMET profiles
    4. Executes the comparison
    5. Outputs results to file or console
    """
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="Compare ADMET score similarity between chemicals.")
    parser.add_argument("--target", required=True, help="JSON file containing the target ADMET profile")
    parser.add_argument("--candidates", required=True, help="JSON file containing a list of candidate profiles")
    parser.add_argument("--output", help="Output JSON file for results")
    parser.add_argument("--profile", default="default", help="Weight profile to use (e.g., default, safety, pharmacokinetics)")
    parser.add_argument("--weights-file", default=".opencode/skills/similarity-scoring/config/weights.json", help="Path to weights configuration file")
    
    # Parse command-line arguments
    args = parser.parse_args()
    
    # Load weights from configuration file
    try:
        with open(args.weights_file, 'r') as f:
            all_weights = json.load(f)
            selected_weights = all_weights.get(args.profile, all_weights.get("default", {}))
    except FileNotFoundError:
        print(f"Warning: Weights file not found at {args.weights_file}. Using uniform weights.")
        selected_weights = {}
    
    # Load target ADMET profile
    with open(args.target, 'r') as f:
        target_profile = json.load(f)
        
    # Load candidate ADMET profiles and ensure proper format
    with open(args.candidates, 'r') as f:
        candidates = json.load(f)
        
        # Reformat candidates if they are not in the expected structure
        if candidates and not isinstance(candidates[0], dict) or 'profile' not in candidates[0]:
             candidates = [{"id": f"cand_{i}", "profile": p} for i, p in enumerate(candidates)]
    
    # Execute ADMET profile comparison
    results = compare_admet_profiles(target_profile, candidates, selected_weights)
    
    # Output results
    if args.output:
        # Save results to output file
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
    else:
        # Print results to console
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
