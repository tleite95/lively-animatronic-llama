---
name: admet-ai-scoring
description: Predict ADMET (Absorption, Distribution, Metabolism, Excretion, Toxicity) properties of chemical compounds from SMILES strings using ADMET-AI, a local open-source Python package with pretrained graph neural network models. Use this skill whenever the user wants to evaluate pharmacokinetic/toxicological properties of a molecule or list of molecules for all questions regarding ADMET, drug-likeness, or toxicity. Also use for batch screening of compound libraries (CSV of SMILES) for lead optimization or virtual screening filtering. This skill focuses solely on ADMET prediction and endpoint identification. For Molecular Initiating Event (MIE) identification, use the mie-identification skill.
metadata:
    references:
    - references/endpoints.md
---

Predicts pharmacokinetic and toxicity properties of small molecules from their SMILES representation, using [ADMET-AI](https://github.com/swansonk14/admet_ai) — an open-source, locally-run graph neural network (Chemprop-RDKit) trained on 41 ADMET endpoints from the Therapeutics Data Commons. No API key, no network access, and no rate limits required; everything runs on-device after a one-time install.

**Note on admetSAR:** If the user specifically asks for "admetSAR," know that admetSAR (the website at lmmd.ecust.edu.cn) has no public API — it's a rate-limited web form with no documented, stable way to script against it. ADMET-AI is the recommended local substitute: it covers overlapping endpoints, has no rate limits, and is scored competitively against admetSAR on published benchmarks. Mention this substitution to the user briefly if they asked for admetSAR by name.

## Setup (one-time per environment)

Check if it's already installed before reinstalling:

```bash
python3 -c "import admet_ai" 2>/dev/null && echo "already installed" || pip install admet-ai --break-system-packages
```

Installation pulls in RDKit, Chemprop, PyTorch, and other deps, so it can take a few minutes and needs a few GB of disk. The first `ADETModel()` call also downloads pretrained model weights (~cached after first use).

If installation fails with a missing shared library error (e.g. `libXrender.so.1`), that's a system dependency, not a Python one — tell the user to install it via their OS package manager (e.g. `apt-get install -y libxrender1` on Ubuntu/Debian).

## Making predictions

### Quick path: use the bundled script

For most requests, run `scripts/predict_admet.py`, which wraps the ADMET-AI Python API and prints/saves results in a clean format.

**Single molecule:**
```bash
python3 scripts/predict_admet.py --smiles "CC(=O)OC1=CC=CC=C1C(=O)O"
```

**Multiple molecules inline:**
```bash
python3 scripts/predict_admet.py --smiles "CCO" "CC(=O)OC1=CC=CC=C1C(=O)O"
```

**Batch from a CSV** (must have a `smiles` column; add `--smiles-column` if it's named differently):
```bash
python3 scripts/predict_admet.py --input compounds.csv --output predictions.csv
```

The script prints a comprehensive human-readable summary to stdout, covering all ADMET properties organized by category (Absorption, Distribution, Metabolism, Excretion, Toxicity, Physicochemical Properties, and Additional Properties). It identifies relevant endpoints based on prediction values and highlights critical properties for drug development and safety. The script saves the full results to a JSON file when `--output` is specified.

### Direct Python API (for custom pipelines)

When the user wants ADMET predictions integrated into a larger script rather than run standalone, use the library directly:

```python
from admet_ai import ADMETModel

model = ADMETModel()

# Single molecule -> dict of property: value
preds = model.predict(smiles="CC(=O)OC1=CC=CC=C1C(=O)O")

# List of molecules -> pandas DataFrame (index=SMILES, columns=properties)
preds_df = model.predict(smiles=["CCO", "CC(=O)OC1=CC=CC=C1C(=O)O"])
```

Classification properties (e.g. BBB permeability, DILI, Ames mutagenicity, hERG inhibition) return a probability between 0 and 1 that the molecule has that property — not a hard yes/no. Regression properties (e.g. half-life, solubility, clearance) return the predicted value directly, in the units documented in `references/endpoints.md`.


## Interpreting and presenting results

- **Always provide full detailed output when requesting ADMET scores.** Include absorption, distribution, metabolism, excretion, toxicity, and all other relevant scores.
- **Never present a raw 41-column table as the whole answer.** Summarize the properties most relevant to what the user asked (e.g. if they asked about oral drugs, lead with absorption/bioavailability/CYP metabolism; if they asked about safety, lead with the toxicity endpoints).
- State classification outputs as probabilities/likelihoods, not certainties ("~78% probability of BBB permeability" rather than "this molecule crosses the BBB").
- These are machine-learning predictions from a model trained on public datasets, not experimental measurements or a substitute for wet-lab ADMET assays or regulatory toxicology — say so if the user seems to be treating results as a final safety determination.

## Integration with Other Skills

This skill focuses solely on ADMET prediction and endpoint identification. For Molecular Initiating Event (MIE) identification and Adverse Outcome Pathway (AOP) analysis, use the `mie-identification` skill:

```bash
# First predict ADMET properties
python3 scripts/predict_admet.py --smiles "CC(=O)OC1=CC=CC=C1C(=O)O" --output admet_results.json

# Then identify MIEs from the predictions
python3 scripts/predict_mie.py --smiles "CC(=O)OC1=CC=CC=C1C(=O)O" --output mie_results.json
```

The `mie-identification` skill uses the mapping files (`admet_ai_mie_to_aopwiki_map.json` and `admet_aop_candidate_mapping.json`) to connect ADMET predictions to known biological mechanisms and calculate risk scores for specific AOP events.

### Example: MIE Prediction

```python
import json
from admet_ai import ADMETModel

# Load mapping files
with open('references/admet_ai_mie_to_aopwiki_map.json') as f:
    mie_mapping = json.load(f)

with open('references/admet_aop_candidate_mapping.json') as f:
    aop_mapping = json.load(f)

# Make ADMET predictions
model = ADMETModel()
preds = model.predict(smiles="CC(=O)OC1=CC=CC=C1C(=O)O")

# Identify potential MIEs
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

# Sort by confidence (prediction value)
potential_miess.sort(key=lambda x: x['value'], reverse=True)

print("Potential Molecular Initiating Events:")
for mie in potential_miess:
    print(f"  - {mie['mie_name']} (confidence: {mie['value']:.3f})")
    print(f"    AOP IDs: {mie['aop_ids']}")
```

### Example: AOP Risk Assessment

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

# Calculate combined risk score using the provided combination logic
if 'combine_with' in herg_data and all(p in preds for p in herg_data['combine_with']):
    logP = preds['logP']
    bbb_prob = preds['BBB_Martins']
    
    # Apply the weighted combination formula from the mapping
    logP_contribution = 1.0 if logP >= 3 else 0.5 if logP >= 2 else 0.0
    risk_score = 0.85 * herg_prob + 0.10 * logP_contribution + 0.05 * bbb_prob
    risk_score = min(max(risk_score, 0), 1)  # Clamp between 0 and 1
else:
    risk_score = herg_prob

print(f"hERG cardiac toxicity risk score: {risk_score:.3f}")
print(f"Risk level: {'High' if risk_score > 0.7 else 'Medium' if risk_score > 0.4 else 'Low'}")
```