#!/usr/bin/env python3
"""
Predict Molecular Initiating Events (MIEs) from ADMET predictions.

This script takes ADMET predictions and maps them to potential MIEs
using the provided mapping files. It focuses on MIE identification only.
Full AOP pathway analysis is handled by the AOP expert agent.
"""

import json
import argparse
import sys
from pathlib import Path


def load_mapping_files():
    """Load MIE mapping files."""
    base_dir = Path(__file__).parent.parent
    
    mie_map_path = base_dir / "references" / "admet_ai_mie_to_aopwiki_map.json"
    aop_map_path = base_dir / "references" / "admet_aop_candidate_mapping.json"
    
    with open(mie_map_path) as f:
        mie_mapping = json.load(f)
    
    with open(aop_map_path) as f:
        aop_mapping = json.load(f)
    
    return mie_mapping, aop_mapping


def load_admet_predictions(admet_file):
    """Load ADMET predictions from file."""
    with open(admet_file, 'r') as f:
        return json.load(f)


def map_to_miess(preds, mie_mapping):
    """Map ADMET predictions to potential MIEs."""
    potential_miess = []
    
    for assay, value in preds.items():
        if assay in [m['admet_ai_label'] for m in mie_mapping['mappings']]:
            mapping = next(m for m in mie_mapping['mappings'] if m['admet_ai_label'] == assay)
            potential_miess.append({
                'assay': assay,
                'value': value,
                'mie_name': mapping['primary_ke_mapping']['ke_title'],
                'mie_id': mapping['primary_ke_mapping']['ke_id'],
                'aop_ids': mapping['primary_ke_mapping']['aop_ids_where_mie'],
                'confidence': mapping.get('confidence', 0.9)
            })
    
    # Sort by confidence (prediction value) descending
    potential_miess.sort(key=lambda x: x['value'], reverse=True)
    
    return potential_miess


def calculate_risk_scores(preds, aop_mapping):
    """Calculate risk scores for specific MIE events."""
    risk_assessments = []
    
    for mapping in aop_mapping:
        key = mapping['key']
        if key not in preds:
            continue
            
        base_prob = preds[key]
        
        # Calculate combined risk score if combination logic is provided
        if 'combine_with' in mapping and all(p in preds for p in mapping['combine_with']):
            # Apply the combination logic from the mapping
            components = {}
            
            for prop in mapping['combine_with']:
                if prop == 'logP':
                    logP = preds['logP']
                    components['logP_ge_3'] = 1.0 if logP >= 3 else 0.5 if logP >= 2 else 0.0
                elif prop == 'BBB_Martins':
                    components['p_BBB_Martins'] = preds['BBB_Martins']
                elif prop.endswith('_alert'):
                    # Handle alert flags
                    components[f'alert_{prop}'] = 1.0 if preds.get(prop, 0) > 0.5 else 0.0
                else:
                    components[f'p_{prop}'] = preds[prop]
            
            # Apply the weighted sum formula
            formula = mapping['combine_logic']['formula']
            risk_score = eval(formula, {}, components)
            risk_score = min(max(risk_score, 0), 1)  # Clamp between 0 and 1
        else:
            risk_score = base_prob
        
        # Determine risk level
        if risk_score > 0.7:
            risk_level = 'High'
        elif risk_score > 0.4:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'
        
        risk_assessments.append({
            'event': mapping['mapped_event'],
            'event_id': mapping['actual_event_id'],
            'base_probability': base_prob,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'confidence': mapping['confidence']
        })
    
    # Sort by risk score descending
    risk_assessments.sort(key=lambda x: x['risk_score'], reverse=True)
    
    return risk_assessments


def print_mie_summary(smiles, potential_miess, risk_assessments):
    """Print a human-readable summary of MIE predictions."""
    print(f"\nMIE Prediction Summary for SMILES: {smiles}")
    print("=" * 60)
    
    if potential_miess:
        print("\nPotential Molecular Initiating Events:")
        print("-" * 60)
        for mie in potential_miess[:5]:  # Show top 5
            print(f"  {mie['mie_name']}")
            print(f"    - Assay: {mie['assay']}")
            print(f"    - Confidence: {mie['value']:.3f}")
            print(f"    - MIE ID: {mie['mie_id']}")
            print(f"    - AOP IDs: {mie['aop_ids']}")
            print(f"    - Mapping Confidence: {mie['confidence']}")
    else:
        print("\nNo significant Molecular Initiating Events identified.")
    
    if risk_assessments:
        print("\nRisk Assessment for AOP Events:")
        print("-" * 60)
        for assessment in risk_assessments[:3]:  # Show top 3
            print(f"  {assessment['event']}")
            print(f"    - Event ID: {assessment['event_id']}")
            print(f"    - Risk Score: {assessment['risk_score']:.3f}")
            print(f"    - Risk Level: {assessment['risk_level']}")
            print(f"    - Base Probability: {assessment['base_probability']:.3f}")
            print(f"    - Confidence: {assessment['confidence']}")
    else:
        print("\nNo risk assessments available.")
    
    print("\nNote: These are machine-learning predictions and should be validated")
    print("with experimental data and expert review before making regulatory decisions.")
    print("For full AOP pathway analysis, use the AOP expert agent.")
    print("For full AOP pathway analysis, use the AOP expert agent.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Predict Molecular Initiating Events (MIEs) from ADMET predictions."
    )
    
    parser.add_argument(
        '--admet-file',
        help='JSON file containing ADMET predictions from admet-ai-scoring',
        required=True
    )
    
    parser.add_argument(
        '--output',
        help='Output file path for detailed results (JSON)',
        default=None
    )
    
    args = parser.parse_args()
    
    # Load mapping files
    mie_mapping, aop_mapping = load_mapping_files()
    
    # Load ADMET predictions from file
    print(f"Loading ADMET predictions from {args.admet_file}...")
    admet_results = load_admet_predictions(args.admet_file)
    
    # Process each SMILES
    all_results = {}
    
    for smiles, preds in admet_results.items():
        print(f"\nProcessing SMILES: {smiles}")
        
        # Map to MIEs
        potential_miess = map_to_miess(preds, mie_mapping)
        
        # Calculate risk scores
        risk_assessments = calculate_risk_scores(preds, aop_mapping)
        
        # Store results
        all_results[smiles] = {
            'admet_predictions': preds,
            'potential_miess': potential_miess,
            'risk_assessments': risk_assessments
        }
        
        # Print summary
        print_mie_summary(smiles, potential_miess, risk_assessments)
    
    # Save detailed results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\nDetailed results saved to: {args.output}")


if __name__ == '__main__':
    main()