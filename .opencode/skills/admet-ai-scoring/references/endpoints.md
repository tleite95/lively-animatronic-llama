# ADMET-AI Endpoints Documentation

This document describes the 41 ADMET endpoints predicted by the ADMET-AI model.

## Classification Endpoints (Probability Output)

These endpoints return a probability between 0 and 1, where higher values indicate a higher likelihood of the property.

### Absorption
- **Caco2**: Permeability through Caco-2 cells (intestinal absorption model)
- **Pgp**: P-glycoprotein substrate/inhibitor probability
- **BBB_Martins**: Blood-brain barrier permeability (Martins model)
- **BBB_Adindo**: Blood-brain barrier permeability (Adindo model)
- **OAT**: Organic anion transporter inhibition
- **OCT**: Organic cation transporter inhibition
- **drug_likeness**: Overall drug-likeness score

### Distribution
- **VDss**: Volume of distribution at steady state
- **FUP**: Fraction unbound in plasma

### Metabolism
- **CYP1A2**: CYP1A2 inhibition
- **CYP2C19**: CYP2C19 inhibition
- **CYP2C9**: CYP2C9 inhibition
- **CYP2D6**: CYP2D6 inhibition
- **CYP3A4**: CYP3A4 inhibition
- **CYP2D6_2C9_3A4**: Combined CYP2D6, 2C9, and 3A4 inhibition

### Excretion
- **half_life**: Half-life prediction
- **clearance**: Hepatic clearance prediction
- **Vd**: Volume of distribution

### Toxicity
- **AMES**: Ames mutagenicity test result
- **DILI**: Drug-induced liver injury probability
- **hERG**: hERG channel inhibition (cardiotoxicity marker)
- **hERG2**: Alternative hERG inhibition model
- **skin_reaction**: Skin sensitization probability
- **eye_corrosion**: Eye corrosion probability
- **mutagenicity**: General mutagenicity probability
- **tumorigenicity**: Tumorigenicity probability
- **irritation**: Skin/eye irritation probability

## Regression Endpoints (Numerical Output)

These endpoints return numerical values with specific units.

### Physicochemical Properties
- **logP**: Octanol-water partition coefficient
- **solubility**: Aqueous solubility (mg/mL)
- **Lipinski_violation**: Number of Lipinski's rule of five violations

### Absorption
- **Caco2_Papp**: Caco-2 apparent permeability (nm/s)
- **Pgp_Papp**: P-glycoprotein permeability (nm/s)

### Metabolism
- **CYP1A2_IC50**: CYP1A2 IC50 value (µM)
- **CYP2C19_IC50**: CYP2C19 IC50 value (µM)
- **CYP2C9_IC50**: CYP2C9 IC50 value (µM)
- **CYP2D6_IC50**: CYP2D6 IC50 value (µM)
- **CYP3A4_IC50**: CYP3A4 IC50 value (µM)

### Toxicity
- **LD50**: Lethal dose 50 (mg/kg)
- **hERG_IC50**: hERG IC50 value (µM)

## Usage Notes

1. **Classification endpoints**: Values close to 1 indicate high probability, values close to 0 indicate low probability
2. **Regression endpoints**: Values should be interpreted according to their specific units
3. **Thresholds**: For binary decisions, typical thresholds are:
   - 0.5 for classification endpoints (probability > 0.5 = positive)
   - Endpoint-specific thresholds for regression endpoints (e.g., hERG IC50 < 10 µM may be considered significant)
4. **Uncertainty**: All predictions have inherent uncertainty and should be validated with experimental data

## References

- ADMET-AI model trained on Therapeutics Data Commons (TDC) datasets
- Endpoints cover key pharmacokinetic and toxicological properties relevant to drug discovery
- Model architecture: Chemprop-RDKit graph neural network