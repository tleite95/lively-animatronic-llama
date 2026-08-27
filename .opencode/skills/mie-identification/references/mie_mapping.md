# MIE Mapping Documentation

This document describes the mapping between ADMET-AI assay labels and Molecular Initiating Events (MIEs) in the AOP-Wiki database.

## Overview

The ADMET-AI package provides predictions for various ADMET properties, including toxicity endpoints that can serve as Molecular Initiating Events (MIEs). This mapping connects ADMET-AI assay labels to known MIEs in the AOP-Wiki database. The ADMET-AI scoring skill focuses solely on identifying potential MIEs and linking them to AOP-Wiki Key Events. Full AOP pathway prediction and analysis is handled by the AOP expert agent.

## Mapping Files

### 1. admet_ai_mie_to_aopwiki_map.json

This file maps ADMET-AI assay labels to AOP-Wiki Key Events and Molecular Initiating Events:

- **Purpose**: Connect ADMET-AI assay outputs to known biological mechanisms in the AOP-Wiki
- **Content**: Maps assay labels like "NR-AR", "NR-AhR", "hERG", "AMES" to corresponding Key Event IDs and titles, by first identifying the corresponding MIE
- **Usage**: Used to identify potential MIEs from ADMET predictions and link them to known AOPs, which will be done by the aop-expert agent

### 2. admet_aop_candidate_mapping.json

This file maps ADMET properties to potential AOP candidate events:

- **Purpose**: Provide confidence scores and combination logic for mapping ADMET properties to AOP events
- **Content**: Contains mappings with confidence scores, risk definitions, and combination logic for multiple ADMET properties
- **Usage**: Used to assess the likelihood of specific AOP events based on ADMET predictions. This is for MIE identification only, not full pathway prediction.


## Usage Examples

### Example 1: Mapping ADMET Predictions to MIEs

```python
import json
from admet_ai import ADMETModel

# Load mapping files
with open('admet_ai_mie_to_aopwiki_map.json') as f:
    mie_mapping = json.load(f)

with open('admet_aop_candidate_mapping.json') as f:
    aop_mapping = json.load(f)

# Make ADMET predictions
model = ADMETModel()
preds = model.predict(smiles="CC(=O)OC1=CC=CC=C1C(=O)O")

# Map predictions to MIEs
for assay, value in preds.items():
    if assay in [m['admet_ai_label'] for m in mie_mapping['mappings']]:
        mapping = next(m for m in mie_mapping['mappings'] if m['admet_ai_label'] == assay)
        print(f"{assay}: {value:.3f} → {mapping['primary_ke_mapping']['ke_title']}")
```

### Example 2: Assessing AOP Risk from ADMET Predictions

```python
import json
from admet_ai import ADMETModel

# Load mapping files
with open('admet_aop_candidate_mapping.json') as f:
    aop_mapping = json.load(f)

# Make ADMET predictions
model = ADMETModel()
preds = model.predict(smiles="CC(=O)OC1=CC=CC=C1C(=O)O")

# Assess AOP risk for hERG
herg_data = next(m for m in aop_mapping if m['key'] == 'hERG')
herg_prob = preds['hERG']

# Calculate combined risk score
if 'combine_with' in herg_data and all(p in preds for p in herg_data['combine_with']):
    # Apply combination logic
    logP = preds['logP']
    bbb_prob = preds['BBB_Martins']
    
    # Simple weighted combination
    risk_score = 0.85 * herg_prob + 0.10 * (1 if logP >= 3 else 0.5 if logP >= 2 else 0) + 0.05 * bbb_prob
    risk_score = min(max(risk_score, 0), 1)  # Clamp between 0 and 1
else:
    risk_score = herg_prob

print(f"hERG cardiac toxicity risk: {risk_score:.3f}")
```

## Integration with AOP Analysis

The MIE mappings enable integration with AOP analysis workflows:

1. **ADMET Prediction**: Use ADMET-AI to predict ADMET properties
2. **MIE Identification**: Map predictions to potential MIEs using the mapping files
3. **AOP Linking**: Use the aop-xml skill to retrieve AOP data for identified MIEs (handled by AOP expert agent)
4. **Risk Assessment**: Combine MIE confidence scores with AOP data for comprehensive risk assessment (handled by AOP expert agent)

## Best Practices

1. **Use Multiple Signals**: Combine multiple ADMET properties for more robust MIE identification
2. **Consider Confidence Scores**: Use the confidence scores in the mapping files to weight predictions
3. **Validate with Known Data**: Cross-reference predictions with known chemical-AOP associations
4. **Context Matters**: Consider biological context (species, tissue, exposure route) when interpreting MIEs
5. **Uncertainty**: Clearly communicate the probabilistic nature of predictions
6. **Focus on MIEs**: This skill identifies potential MIEs only. For full AOP pathway analysis, use the AOP expert agent

## Limitations

1. **Model Limitations**: ADMET-AI predictions are based on machine learning models and may not capture all biological mechanisms
2. **Mapping Limitations**: Not all ADMET properties have direct MIE equivalents in AOP-Wiki
3. **Species Differences**: AOPs may vary between species; mappings are primarily based on mammalian data
4. **Mechanistic Gaps**: Some MIEs may involve complex mechanisms not fully captured by ADMET assays

## References

- ADMET-AI: https://github.com/swansonk14/admet_ai
- AOP-Wiki: https://aopwiki.org
- OECD AOP Knowledge Base: https://aopwiki.org/downloads