---
name: confidence-scoring
description: Evaluate how confident the constructor should be in the selected pathway step and the updated pathway overall, using only evidence from the current workflow state and any retrieved database/literature support. Use this as a sub-skill inside `aop-constructor.md`.
---

## Inputs
The constructor should inspect:
- `chemical`
- `AOP_pathways`
- `MIEs`
- `candidates`
- `similarity_scores`
- `rejected_candidates`
- `provenance` or evidence metadata if available
- `decision_history`
- `termination_reason`
- any retrieved citations or database hits
- `iteration_count`
- `MAX_ITERATIONS` or equivalent workflow limit

## Required outputs
Return **only JSON** with this shape:

```json
{
  "selected_candidate": {
    "name": "",
    "type": "KE",
    "confidence": 0.0,
    "similarity": 0.0,
    "reasoning": ""
  },
  "updated_pathway": [
    {
      "event": "",
      "type": "MIE|KE|AO",
      "score": 0.0,
      "provenance": []
    }
  ],
  "confidence_score": 0.0,
  "confidence_breakdown": {
    "mie_foundation": 0.0,
    "pathway_confidence": 0.0,
    "similarity_consistency": 0.0,
    "reasoning_quality": 0.0,
    "pathway_length_penalty": 0.0,
    "weights": {
      "mie_foundation": 0.30,
      "pathway_confidence": 0.40,
      "similarity_consistency": 0.15,
      "reasoning_quality": 0.10,
      "pathway_length": 0.05
    }
  },
  "uncertainty": 0.0,
  "decision_risk": "low|medium|high",
  "next_action": "expand|prune|branch|terminate",
  "is_ao_reached": false,
  "termination_reason": "",
  "decision_reason": "",
  "rejected_candidates": []
}
```

## Scoring method
Use the following weighted scoring approach. For quantitative components, the orchestrator can use `scoring_utils.py` within this skill directory to calculate metrics from the current state.

### Final formula
Compute:

confidence\_score =
0.30 \cdot mie\_foundation +
0.40 \cdot pathway\_confidence +
0.15 \cdot similarity\_consistency +
0.10 \cdot reasoning\_quality +
0.05 \cdot pathway\_length\_penalty
$$

Bound the final result to $$[0.0, 1.0]$$.

### 1) MIE foundation
Use the average confidence of the current MIEs as the foundation.

Higher if:
- MIEs are well-supported by the `admet-mie` agent
- MIEs match known liabilities or reactive features
- the chemical has a clear initiating liability

Lower if:
- MIEs are speculative
- MIE confidence is weak or missing

**Implementation guidance:**
- average the MIE confidence values
- slightly reduce the MIE contribution as iteration count increases, since later iterations should rely more on pathway evidence than initial MIE support

### 2) Pathway confidence
Use the confidence scores on the pathway steps themselves.

Higher if:
- each step follows logically from the previous one
- transitions are biologically plausible
- MIE → KE and KE → AO transitions are coherent
- the pathway is short and focused

Lower if:
- steps are disconnected
- the pathway repeats or stagnates
- the AO is speculative

**Implementation guidance:**
- compute a weighted average of pathway step scores
- use exponential decay so recent steps matter more
- boost transition confidence for:
  - `MIE -> KE`
  - `KE -> AO`

### 3) Similarity consistency
Assess whether the candidate similarity scores are internally consistent.

Higher if:
- similarity scores are close to each other in a sensible range
- the top candidate is clearly above weaker alternatives

Lower if:
- scores are inconsistent or tied
- no candidate stands out

**Implementation guidance:**
- compute the standard deviation of similarity scores
- convert lower spread into higher consistency
- if there is only one score or no score, use a reasonable default rather than failing

### 4) Reasoning quality
Assess the quality of the selected candidate’s reasoning.

Higher if:
- reasoning is specific and mechanistic
- reasoning references concrete evidence or database support
- scientific language is clear and not generic

Lower if:
- reasoning is vague
- reasoning repeats labels without explanation
- reasoning has no evidence trail

**Implementation guidance:**
- favor longer, specific reasoning over short generic text
- look for scientific terms such as `evidence`, `study`, `analysis`, `validated`, `confirmed`, `database`, `mechanism`
- do not reward verbosity alone; the reasoning must be substantive

### 5) Pathway length penalty
Apply a mild penalty to overly long pathways.

Higher score if:
- the pathway is short and coherent
- AO is reached without unnecessary repetition

Lower score if:
- the pathway grows long without converging
- the graph repeats similar KEs

**Implementation guidance:**
- no penalty for a short pathway
- penalize once the pathway exceeds an optimal length
- apply a stronger penalty if it becomes excessively long

## Decision logic
Set `next_action` as follows:
- `expand` when the selected candidate is plausible and evidence-supported
- `prune` when weak candidates should be removed but expansion may continue
- `branch` when multiple candidates are similarly plausible
- `terminate` when no defensible pathway extension exists or AO is reached

## Confidence guidelines
Use a bounded score from 0.0 to 1.0:
- `0.0-0.3`: weak / highly uncertain
- `0.3-0.6`: moderate / partially supported
- `0.6-0.8`: strong / well-supported
- `0.8-1.0`: very strong / highly consistent

## Termination rules
Set `is_ao_reached = true` only when:
- the pathway has reached a defensible adverse outcome
- the final step is biologically plausible
- the evidence chain supports the conclusion

Set `termination_reason` when:
- AO is reached
- no further valid expansion exists
- evidence is insufficient
- the pathway is repeating or stagnating

## Output constraints
- Return JSON only
- Do not add markdown
- Do not add prose outside JSON
- Do not invent evidence
- Do not score a candidate higher than the evidence supports

## Suggested constructor prompt addition
Add this instruction to `aop-constructor.md`:

> Evaluate pathway confidence using the constructor confidence skill. Base your score on MIE support, weighted pathway coherence, similarity consistency, reasoning quality, and a pathway-length penalty. Return both a single `confidence_score` and a detailed `confidence_breakdown` including weights and step-level rationale.