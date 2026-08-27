---
name: mie-identification
description: Identify Molecular Initiating Events (MIEs) by mapping ADMET predictions and endpoints to known biological mechanisms in the AOP-Wiki database. Use this skill when the user wants to identify potential biological mechanisms of action, link ADMET predictions to adverse outcome pathways, or assess the likelihood of specific AOP events based on ADMET data. This skill focuses solely on MIE identification and risk assessment, while full AOP pathway prediction and analysis is handled by the AOP expert agent. This skill only loads ADMET predictions from a file and must be used in conjunction with the admet-ai-scoring skill.
---

## Overview

MIE identification is a critical step in Adverse Outcome Pathway (AOP) analysis. This skill:

1. Maps ADMET assay labels to AOP-Wiki Key Events and Molecular Initiating Events using the `admet_ai_mie_to_aopwiki_map.json` file and the `admet_aop_candidate_mapping.json` file
2. Calculates risk and confidence scores for specific MIEs based on ADMET predictions
3. Provides confidence scores for robust MIE identification
4. Generates human-readable summaries of potential MIEs

**Note**: This skill focuses on MIE identification only. Full AOP pathway prediction, retrieval of AOP data, and comprehensive AOP analysis is handled by the AOP expert agent. This skill does not perform ADMET predictions and must be used with ADMET results from the admet-ai-scoring skill.

## Usage

### Using ADMET Results from admet-ai-scoring

The mie-identification skill is designed to work exclusively with ADMET results produced by the admet-ai-scoring skill. This ensures consistency and efficiency in the workflow.

The mie-identification skill can work with ADMET results produced by the admet-ai-scoring skill:

```bash
# First predict ADMET properties using admet-ai-scoring
python3 scripts/predict_admet.py --smiles "CC(=O)OC1=CC=CC=C1C(=O)O" --output admet_results.json

# Then identify MIEs from the ADMET results file
python3 scripts/predict_mie.py --admet-file admet_results.json --output mie_results.json
```

This is the **only** approach supported by this skill. The mie-identification skill does not perform ADMET predictions directly and always requires pre-computed ADMET results from the admet-ai-scoring skill.

### Batch Processing

```bash
# First predict ADMET properties for multiple molecules using admet-ai-scoring
python3 scripts/predict_admet.py --smiles "CCO" "CC(=O)OC1=CC=CC=C1C(=O)O" --output admet_results.json

# Then identify MIEs from the ADMET results file
python3 scripts/predict_mie.py --admet-file admet_results.json --output mie_results.json
```

## MIE Mapping Files

### 1. admet_ai_mie_to_aopwiki_map.json

Maps ADMET-AI assay labels to AOP-Wiki Key Events:

- **Purpose**: Connect ADMET assay outputs to known biological mechanisms
- **Content**: Maps assay labels (NR-AR, NR-AhR, hERG, AMES, etc.) to Molecular Initiating Event IDs and titles
- **Usage**: Identify potential MIEs from ADMET predictions and link them to known AOPs

### 2. admet_aop_candidate_mapping.json

Provides confidence scores and combination logic:

- **Purpose**: Assess likelihood of specific AOP events based on ADMET predictions
- **Content**: Contains mappings with confidence scores, risk definitions, and combination logic
- **Usage**: Calculate risk and confidence scores for AOP events using multiple ADMET properties

## Example: MIE Prediction

```python
import json

# Load mapping files
with open('references/admet_ai_mie_to_aopwiki_map.json') as f:
    mie_mapping = json.load(f)

with open('references/admet_aop_candidate_mapping.json') as f:
    aop_mapping = json.load(f)

# Load ADMET predictions from file (produced by admet-ai-scoring skill)
with open('admet_results.json') as f:
    admet_results = json.load(f)

# Get predictions for a specific SMILES
smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"
preds = admet_results[smiles]

# Map predictions to MIEs
potential_miess = []
for assay, value in preds.items():
    if assay in [m['admet_ai_label'] for m in mie_mapping['mappings']]:
        mapping = next(m for m in mie_mapping['mappings'] if m['admet_ai_label'] == assay)
        potential_miess.append({
            'assay': assay,
            'value': value,
            'mie_name': mapping['primary_ke_mapping']['ke_title'],
            'mie_id': mapping['primary_ke_mapping']['ke_id'],
            'aop_ids': mapping['primary_ke_mapping']['aop_ids_where_mie']
        })

# Sort by confidence
potential_miess.sort(key=lambda x: x['value'], reverse=True)

print("Potential Molecular Initiating Events:")
for mie in potential_miess:
    print(f"  - {mie['mie_name']} (confidence: {mie['value']:.3f})")
    print(f"    AOP IDs: {mie['aop_ids']}")
```

## Example: AOP Risk Assessment

```python
import json
from admet_ai import ADMETModel

# Load mapping files
with open('references/admet_aop_candidate_mapping.json') as f:
    aop_mapping = json.load(f)

# Make ADMET predictions
model = ADMETModel()
preds = model.predict(smiles="CC(=O)OC1=CC=CC=C1C(=O)O")

# Assess risk for hERG-related cardiac toxicity
herg_data = next(m for m in aop_mapping if m['key'] == 'hERG')
herg_prob = preds['hERG']

# Calculate combined risk score
if 'combine_with' in herg_data and all(p in preds for p in herg_data['combine_with']):
    logP = preds['logP']
    bbb_prob = preds['BBB_Martins']
    
    # Apply weighted combination formula
    logP_contribution = 1.0 if logP >= 3 else 0.5 if logP >= 2 else 0.0
    risk_score = 0.85 * herg_prob + 0.10 * logP_contribution + 0.05 * bbb_prob
    risk_score = min(max(risk_score, 0), 1)  # Clamp between 0 and 1
else:
    risk_score = herg_prob

print(f"hERG cardiac toxicity risk score: {risk_score:.3f}")
print(f"Risk level: {'High' if risk_score > 0.7 else 'Medium' if risk_score > 0.4 else 'Low'}")
```

## Integration with Other Skills

### With ADMET-AI Scoring

```bash
# First predict ADMET properties using admet-ai-scoring
python3 scripts/predict_admet.py --smiles "CC(=O)OC1=CC=CC=C1C(=O)O" --output admet_results.json

# Then identify MIEs using the ADMET results file
python3 scripts/predict_mie.py --admet-file admet_results.json --output mie_results.json
```

### With ADMET Secondary Scoring

The MIE identification skill works seamlessly with the ADMET secondary scoring skill to provide comprehensive ADMET analysis:

```bash
# 1. Predict ADMET properties
python3 scripts/predict_admet.py --smiles "CC(=O)OC1=CC=CC=C1C(=O)O" --output admet_results.json

# 2. Identify MIEs from ADMET predictions
python3 scripts/predict_mie.py --admet-file admet_results.json --output mie_results.json

# 3. Run secondary bucket scoring on the same ADMET predictions
python3 score_admet_secondary_buckets.py admet_results.json admet_secondary_bucket_mapping.json -o secondary_scores.json

# 4. Combine results for comprehensive analysis
python3 scripts/combine_results.py --mie-file mie_results.json --secondary-file secondary_scores.json --output combined_results.json
```

**Integration Benefits:**
- **Complementary Analysis**: MIE identification focuses on specific biological mechanisms, while secondary scoring provides broader ADMET context
- **Cross-Validation**: Use secondary bucket scores to validate MIE predictions (e.g., high exposure modifier scores support MIE relevance)
- **Complete Profile**: Get both specific MIE insights and general ADMET risk assessment

**Example Integration Logic:**
```python
import json

# Load both results
with open('mie_results.json') as f:
    mie_results = json.load(f)

with open('secondary_scores.json') as f:
    secondary_results = json.load(f)

# Cross-reference findings
for smiles, mie_data in mie_results.items():
    secondary_data = secondary_results['results'][0]  # Assuming single compound
    
    # Check if high exposure scores support MIE relevance
    exposure_score = secondary_data['bucket_scores']['exposure_modifiers']['score']
    
    for mie in mie_data['potential_miess']:
        if exposure_score > 0.7 and mie['value'] > 0.7:
            print(f"{smiles}: High confidence MIE {mie['mie_name']} with supporting exposure profile")
```

### With AOP Expert Agent
 
The MIE identification skill provides the foundation for full AOP analysis:

1. **MIE Identification**: Use this skill to identify potential MIEs from ADMET predictions
2. **Secondary Scoring**: Use ADMET secondary scoring to assess broader ADMET context
3. **AOP Retrieval**: Use the AOP expert agent to retrieve full AOP data for identified MIEs
4. **Comprehensive Analysis**: Combine MIE confidence scores, secondary bucket scores, and AOP data for robust risk assessment

### With AOP Expert Agent

The MIE identification skill provides the foundation for full AOP analysis:

1. **MIE Identification**: Use this skill to identify potential MIEs from ADMET predictions
2. **AOP Retrieval**: Use the AOP expert agent to retrieve full AOP data for identified MIEs
3. **Comprehensive Analysis**: Combine MIE confidence scores with AOP data for risk assessment

## Best Practices

1. **Always use admet-ai-scoring first**: Use the admet-ai-scoring skill to obtain ADMET predictions before running MIE identification
2. **Use Multiple Signals**: Combine multiple ADMET properties for more robust MIE identification
3. **Consider Confidence Scores**: Use the confidence scores in mapping files to weight predictions
4. **Validate with Known Data**: Cross-reference predictions with known chemical-AOP associations
5. **Combine with Experimental Data**: MIE predictions should be validated with experimental data before making regulatory decisions
6. **Use Secondary Scoring for Context**: Run ADMET secondary scoring to get broader ADMET context that can support or challenge MIE predictions
7. **Consult Experts**: Always consult toxicology experts for final risk assessments
8. **Ensure ADMET file compatibility**: The ADMET results file must be in the format produced by the admet-ai-scoring skill

## Workflow Integration with Secondary Scoring

The MIE identification skill is designed to work in tandem with the ADMET secondary scoring skill:

### Recommended Workflow

1. **Primary ADMET Prediction** (admet-ai-scoring)
   - Generate comprehensive ADMET predictions for your compound(s)

2. **MIE Identification** (mie-identification)
   - Map ADMET predictions to specific Molecular Initiating Events
   - Get confidence scores and risk assessments for potential MIEs

3. **Secondary Bucket Scoring** (admet-secondary-scoring)
   - Analyze non-NR/SR ADMET outputs into heuristic buckets
   - Get exposure modifiers, liability phenotypes, and chemistry quality signals

4. **Combined Analysis**
   - Cross-reference MIE predictions with secondary bucket scores
   - Use exposure modifiers to validate MIE relevance
   - Combine liability phenotypes with MIE risk assessments

### Integration Examples

**Example 1: Validating MIE Relevance with Exposure Scores**
```python
# If a compound shows high MIE confidence for hERG inhibition
# but low exposure modifier scores, the MIE may not be biologically relevant

mie_score = 0.85  # High hERG MIE confidence
exposure_score = 0.2  # Low systemic exposure

if mie_score > 0.7 and exposure_score < 0.3:
    print("Warning: High MIE confidence but low exposure - MIE may not be relevant")
```

**Example 2: Enhancing Risk Assessment**
```python
# Combine MIE risk scores with liability phenotype scores

mie_risk = 0.75  # Medium-high MIE risk
liability_score = 0.85  # High liability phenotype score

combined_risk = 0.6 * mie_risk + 0.4 * liability_score
print(f"Enhanced risk score: {combined_risk:.2f}")
```

## Limitations

- MIE predictions are based on machine learning models and should not replace experimental validation
- The skill identifies potential MIEs but does not predict full AOP pathways
- Risk scores are relative and should be interpreted in context
- Always validate predictions with experimental data and expert review
- Secondary scoring provides complementary information but should not replace specific MIE analysis

## Output Format

The `predict_mie.py` script produces:

1. **Human-readable summary**: Printed to stdout with top potential MIEs and risk assessments
2. **JSON output**: Detailed results including all predictions, MIEs, and risk assessments (when `--output` is specified)

### Integration with Secondary Scoring Output

When used together with ADMET secondary scoring, the combined output structure includes:

```json
{
  "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
  "mie_analysis": {
    "potential_miess": [...],
    "risk_assessments": [...]
  },
  "secondary_analysis": {
    "bucket_scores": {
      "exposure_modifiers": {"score": 0.65, "level": "moderate"},
      "liability_phenotypes": {"score": 0.45, "level": "low"},
      "chemistry_quality": {"score": 0.30, "level": "low"}
    },
    "family_scores": {
      "systemic_exposure": {"score": 0.65, "level": "moderate"},
      "broad_toxicity": {"score": 0.45, "level": "low"}
    }
  },
  "combined_assessment": {
    "overall_risk": "Medium",
    "confidence": 0.82,
    "flags": ["high_mie_confidence_with_medium_exposure"]
  }
}
```

This combined format enables comprehensive risk assessment by considering both specific MIE mechanisms and broader ADMET context.

Example JSON output structure:

```json
{
  "CC(=O)OC1=CC=CC=C1C(=O)O": {
    "admet_predictions": {
      "hERG": 0.123,
      "BBB_Martins": 0.456,
      "logP": 2.345,
      ...
    },
    "potential_miess": [
      {
        "assay": "hERG",
        "value": 0.123,
        "mie_name": "Inhibition of hERG potassium channels",
        "mie_id": "KE-1234",
        "aop_ids": ["AOP-5678"],
        "confidence": 0.9
      }
    ],
    "risk_assessments": [
      {
        "event": "Cardiac toxicity via hERG inhibition",
        "event_id": "AOP-5678",
        "base_probability": 0.123,
        "risk_score": 0.156,
        "risk_level": "Low",
        "confidence": 0.85
      }
    ]
  }
}
```

## Troubleshooting

- **Missing mapping files**: Ensure the `references` directory is in the same location as the script
- **No MIEs identified**: Check that ADMET predictions include assays covered by the mapping files
- **Low confidence scores**: Consider using additional data sources or experimental validation
- **ADMET file format issues**: Ensure the ADMET results file is in the correct format produced by the admet-ai-scoring skill
- **Integration with secondary scoring**: Ensure both skills are using the same ADMET predictions file
- **Inconsistent results**: Check that the ADMET predictions file contains all required fields for both MIE identification and secondary scoring
- **Missing secondary bucket scores**: Verify that the `admet_secondary_bucket_mapping.json` file is present and properly configured

For more information, see the detailed documentation in the `references` directory.