---
name: similarity-scoring
description: Predict and analyze the similarity of ADMET profiles between different chemical compounds using vector similarity (cosine similarity). This skill helps identify compounds with similar pharmacokinetic or toxicological profiles to a target molecule for lead optimization or toxicity benchmarking.
---

# Similarity Scoring Skill

This skill provides capabilities to predict and analyze the similarity in ADMET (Absorption, Distribution, Metabolism, Excretion, Toxicity) scores between different chemical compounds.

## Overview
Rather than relying on a hard-coded orchestrator, this skill provides a methodology for an agent to compare ADMET profiles. It treats a compound's ADMET predictions as a high-dimensional vector and calculates the similarity (typically cosine similarity) between the target compound and a set of candidates.

## Core Methodology
1. **Vectorization**: Convert the ADMET properties into a numerical vector. 
   - **Important**: Only properties present in **both** the target and the candidate compound are used for the calculation. Missing keys are excluded to prevent zero-padding from swaying the similarity score.
2. **Weighted Similarity Calculation**: Use Weighted Cosine Similarity to determine the angle between vectors. This allows specific biologically critical endpoints to have a higher impact on the final score.
   - $\text{similarity} = \frac{\sum (W_i \cdot A_i \cdot B_i)}{\sqrt{\sum (W_i \cdot A_i^2)} \cdot \sqrt{\sum (W_i \cdot B_i^2)}}$
   - Score of 1.0: Identical weighted profiles.
   - Score of 0.0: No similarity.

### Weighting Logic
Weights are assigned based on pharmacological priority to ensure the similarity score reflects biological relevance rather than just numerical overlap:
- **Safety Weights**: Prioritize "deal-breaker" toxicity markers (e.g., hERG, DILI, AMES) to identify similar hazard profiles.
- **Pharmacokinetics (PK) Weights**: Prioritize exposure and movement markers (e.g., logP, Bioavailability, Half-life) to identify similar disposition profiles.
- **Default Weights**: Provide a balanced baseline, slightly elevating gold-standard markers while maintaining a broad chemical fingerprint.

## Workflow Instructions
The agent should follow these steps to perform similarity scoring:

### 1. Data Acquisition
- **Target Compound**: Get the ADMET profile for the target SMILES using the `admet-ai-scoring` and `admet-secondary-scoring` skills. Save to `target.json`.
- **Candidate Compounds**: Get ADMET profiles for the candidate SMILES. Save to `candidates.json` (as a list of objects: `{"id": "...", "profile": {...}}`).
  - **Example `candidates.json`**:
    ```json
    [
      {
        "id": "Compound_A",
        "profile": {"hERG": 0.75, "AMES": 0.12, "logP": 2.4, "Caco2": 0.55}
      },
      {
        "id": "Compound_B",
        "profile": {"hERG": 0.2, "AMES": 0.9, "logP": 1.1, "Caco2": 0.2}
      }
    ]
    ```
    - **NOTE** - this example is not fully finished, the profile should contain 41 ADMET properties
- **Secondary Scores**: Use the `admet-secondary-scoring` skill to get bucketed scores and include those in the similarity vector. ALWAYS include secondary scoring as well

### 2. Computation
Use the provided CLI tool for similarity calculation. You can specify a weight profile (e.g., `safety` or `pharmacokinetics`) to prioritize different property types.

```bash
python .opencode/skills/similarity-scoring/scripts/compare_admet.py --target target.json --candidates candidates.json --profile safety --output results.json
```

**Available Profiles in `config/weights.json`:**
- `default`: Balanced weighting.
- `safety`: High priority on hERG, DILI, and AMES.
- `pharmacokinetics`: High priority on logP, Bioavailability, and BBB permeability.

**Direct Python implementation (if needed):**
```python
from .opencode.skills.similarity_scoring.scripts.compare_admet import compare_admet_profiles
# results = compare_admet_profiles(target_dict, candidates_list, selected_weights)
```

### 3. Analysis and Reporting
- **Ranking**: List compounds in descending order of similarity.
- **Divergence Analysis**: Use the `top_divergence` output from the script to identify which specific ADMET endpoints contribute most to the difference.
- **Contextualization**: Link the most similar toxicity profiles to potential MIEs using the `mie-identification` agent/skill.
  - **Suggested Workflow**:
    1. Identify the top-ranked candidate from similarity results.
    2. Pass the `target.json` and the candidate's profile to the `mie-identification` skill.
    3. Ask: "The candidate [ID] shows a similarity score of [Score] to the target. Based on their shared high-weight endpoints (e.g., [Endpoints]), what common Molecular Initiating Events (MIEs) might explain this similar toxicity profile?"

## Usage Examples
- "Find compounds in this list that have a similar toxicity profile to Aspirin."
- "How similar is the ADMET profile of Compound A compared to Compound B?"
- "Compare the systemic exposure and metabolism of these three lead candidates."

## Integration
- **admet-ai-scoring**: Source of primary ADMET vectors.
- **admet-secondary-scoring**: Source of high-level profile buckets for coarse-grained similarity.
- **mie-identification**: Used to explain *why* a similar ADMET profile leads to similar biological outcomes.