---
name: admet-secondary-scoring
description: Analyzes non-NR/SR ADMET-AI outputs into three heuristic buckets (exposure modifiers, liability phenotypes, chemistry quality signals) for compounds that don't map cleanly to specific MIEs or KEs. It is to be used in parallel with the MIE identification skill to provide a more comprehensive assessment of ADMET profiles.
---

# ADMET Secondary Scoring Skill

Analyzes non-NR/SR ADMET-AI outputs into three heuristic buckets:
- Exposure modifiers
- Liability phenotypes
- Chemistry quality signals

## Overview

This skill provides secondary scoring for ADMET predictions that don't map cleanly to specific Molecular Initiating Events (MIEs) or Key Events (KEs). It categorizes predictions into "families" of effects that may be relevant across multiple Adverse Outcome Pathways (AOPs). It serves as a secondary check for compounds that may not have clear MIEs but still exhibit concerning ADMET profiles.

## Key Features

- **Exposure Modifiers**: Contextual PK/ADME signals affecting biological plausibility
- **Liability Phenotypes**: Broad endpoint or metabolism liabilities
- **Chemistry Quality**: Descriptor-based caution signals
- **Heuristic Scoring**: Uses piecewise functions, identity transforms, and binary inverses
- **Evidence Tracking**: Provides detailed evidence for each score

## Usage

### Command Line

```bash
# Basic usage
python score_admet_secondary_buckets.py predictions.json mapping.json -o results.json
# function is name of python file

# Analyze multiple compounds
python score_admet_secondary_buckets.py compounds.json mapping.json -o all_results.json

# Catalog mode (analyze keys only)
python score_admet_secondary_buckets.py keys.json mapping.json -o catalog.json
```

### Python API

```python
from score_admet_secondary_buckets import analyze_record
import json

# Load predictions and mapping
with open('predictions.json', 'r') as f:
    predictions = json.load(f)

with open('admet_secondary_bucket_mapping.json', 'r') as f:
    mapping_config = json.load(f)

# Analyze a single record
result = analyze_record(predictions, mapping_config)

# Analyze multiple records
results = [analyze_record(pred, mapping_config) for pred in predictions]
```

## Input

### Predictions JSON
ADMET predictions from ADMET-AI, typically containing:
- PK/ADME properties (Bioavailability, HIA, PAMPA, etc.)
- Toxicity endpoints (ClinTox, LD50, etc.)
- Metabolism data (CYP interactions)
- Chemistry descriptors (molecular weight, TPSA, etc.)

### Mapping Configuration
The `admet_secondary_bucket_mapping.json` file defines:
- Which keys to ignore (NR-*, SR-*, etc.)
- Which keys to exclude (high-priority AOP candidates)
- Scoring thresholds (moderate: 0.3, high: 0.7)
- Family definitions with transformation rules
- Annotation groups

## Output

The output JSON contains:

```json
{
  "mode": "scored_records",
  "results": [
    {
      "family_scores": {
        "systemic_exposure": {
          "bucket": "exposure_modifiers",
          "summary": "...",
          "score": 0.65,
          "level": "moderate",
          "evidence": [...]
        },
        ...
      },
      "bucket_scores": {
        "exposure_modifiers": {
          "score": 0.58,
          "level": "moderate"
        },
        ...
      },
      "annotations": {
        "exposure_flags": [
          {"family": "systemic_exposure", "score": 0.65, "level": "moderate"}
        ],
        ...
      },
      "excluded_keys_present": [...],
      "ignored_keys_present": [...],
      "unmapped_keys_present": [...]
    }
  ]
}
```

## Families and Buckets

### Exposure Modifiers
- **systemic_exposure**: Bioavailability, HIA, PAMPA
- **persistence_distribution**: Half-life, VDss, lipophilicity

### Liability Phenotypes
- **broad_toxicity**: ClinTox, LD50
- **metabolic_interaction**: CYP enzyme interactions

### Chemistry Quality
- **druglikeness_caution**: Molecular weight, H-bond acceptors/donors, TPSA, QED, Lipinski violations, stereo centers

## Transformation Rules

The skill supports several transformation types:

- **identity**: Direct mapping (0-1 scale)
- **one_minus**: Inverse mapping (higher raw = lower score)
- **binary_inverse**: Binary inversion (1 becomes 0, 0 becomes 1)
- **piecewise**: Custom breakpoint-based scoring

## Example Workflow

```python
# 1. Generate ADMET predictions
from admet_ai import ADMETModel
model = ADMETModel()
predictions = model.predict(smiles="CCO")

# 2. Save predictions
import json
with open('predictions.json', 'w') as f:
    json.dump(predictions, f)

# 3. Run secondary scoring
from score_admet_secondary_buckets import analyze_record
with open('admet_secondary_bucket_mapping.json', 'r') as f:
    mapping = json.load(f)

result = analyze_record(predictions, mapping)

# 4. Use results
print(f"Exposure modifier score: {result['bucket_scores']['exposure_modifiers']['score']}")
print(f"High risk families: {result['annotations']['exposure_flags']}")
```

## Integration with Other Skills

This skill complements the main ADMET scoring and MIE identification skills:

```python
# Typical workflow
1. Primary ADMET prediction and endpoint identification (admet-ai-scoring)
2. MIE identification (mie-identification)
3. Secondary bucket scoring (admet-secondary-scoring)
4. AOP mapping and confidence scoring
```

## Configuration
The mapping configuration can be customized by:
- Adding new families
- Modifying transformation rules
- Adjusting weights and thresholds
- Adding new annotation groups

## Notes
- Scores are normalized to 0-1 range
- Level thresholds: low (<0.3), moderate (0.3-0.7), high (≥0.7)
- Unmapped keys are reported but not scored
- The skill is designed to work with ADMET-AI v2.x predictions

## Version
1.0