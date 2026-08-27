#!/usr/bin/env python3
"""
Predict ADMET (Absorption, Distribution, Metabolism, Excretion, Toxicity) properties
using ADMET-AI. This script focuses solely on ADMET prediction and endpoint identification without MIE identification.

For MIE identification, use the mie-identification skill separately.
"""

import argparse
import json
import sys
from pathlib import Path
from admet_ai import ADMETModel


def predict_admet(smiles_list, output_file=None):
    """Predict ADMET properties for given SMILES."""
    model = ADMETModel()
    
    if isinstance(smiles_list, str):
        preds = model.predict(smiles=smiles_list)
        results = {smiles_list: preds}
    else:
        preds_df = model.predict(smiles=smiles_list)
        results = preds_df.to_dict('index')
    
    # Save to file if specified - ensure ALL properties are saved
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {output_file}")
    
    # Always return complete results with all available properties
    return results


def print_summary(results):
    """Print a human-readable summary of ADMET predictions."""
    # First, ensure we have all possible ADMET properties
    all_admet_properties = [
        'Caco2', 'Pgp', 'BBB_Martins', 'BBB_Adindo', 'OAT', 'OCT', 'drug_likeness',
        'VDss', 'FUP', 'CYP1A2', 'CYP2C19', 'CYP2C9', 'CYP2D6', 'CYP3A4', 'CYP2D6_2C9_3A4',
        'half_life', 'clearance', 'Vd', 'AMES', 'DILI', 'hERG', 'hERG2',
        'skin_reaction', 'eye_corrosion', 'mutagenicity', 'tumorigenicity', 'irritation',
        'logP', 'solubility', 'Lipinski_violation', 'Caco2_Papp', 'Pgp_Papp',
        'CYP1A2_IC50', 'CYP2C19_IC50', 'CYP2C9_IC50', 'CYP2D6_IC50', 'CYP3A4_IC50',
        'LD50', 'hERG_IC50'
    ]
    
    for smiles, preds in results.items():
        # Ensure all properties are present in the results, even if None
        for prop in all_admet_properties:
            if prop not in preds:
                preds[prop] = None
        
        # Convert to DataFrame-like structure for consistency
        import pandas as pd
        preds_df = pd.DataFrame([preds])
        # Get the first (and only) row from the DataFrame
        row_data = preds_df.iloc[0].to_dict()
        results[smiles] = row_data
        print(f"\n{'='*70}")
        print(f"ADMET PREDICTION SUMMARY FOR: {smiles}")
        print(f"{'='*70}")
        
        # Highlight most relevant properties for toxicity, drug-likeness, and AOPs
        print("\n" + "="*70)
        print("CRITICAL PROPERTIES FOR DRUG DEVELOPMENT & SAFETY")
        print("="*70)
        
        critical_properties = [
            ('Drug-Likeness', 'drug_likeness', 'Overall drug-likeness score'),
            ('BBB Permeability', 'BBB_Martins', 'Blood-brain barrier permeability'),
            ('Hepatotoxicity (DILI)', 'DILI', 'Drug-induced liver injury probability'),
            ('Cardiotoxicity (hERG)', 'hERG', 'hERG channel inhibition probability'),
            ('Mutagenicity (AMES)', 'AMES', 'Ames mutagenicity test result'),
            ('LogP', 'logP', 'Octanol-water partition coefficient'),
            ('Solubility', 'solubility', 'Aqueous solubility (mg/mL)'),
            ('Half-Life', 'half_life', 'Half-life prediction'),
            ('Clearance', 'clearance', 'Hepatic clearance prediction')
        ]
        
        print("\nKey Properties:")
        print("-" * 70)
        
        for name, prop, description in critical_properties:
            if prop in preds and preds[prop] is not None:
                value = preds[prop]
                if prop in ['drug_likeness', 'BBB_Martins', 'DILI', 'hERG', 'AMES']:
                    # Classification properties
                    print(f"  {name}: {value:.3f} (probability)")
                    if value > 0.7:
                        print(f"    ⚠️  HIGH RISK: {description}")
                    elif value > 0.4:
                        print(f"    ⚠️  MODERATE RISK: {description}")
                    else:
                        print(f"    ✓  LOW RISK: {description}")
                else:
                    # Regression properties
                    print(f"  {name}: {value:.3f}")
                    print(f"    Info: {description}")
            else:
                print(f"  {name}: Not available")
                print(f"    Info: {description}")
        
        # Print all ADMET properties in detailed format
        print("\n" + "="*70)
        print("COMPLETE ADMET PROPERTIES BY CATEGORY")
        print("="*70)
        
        # Organize properties by category
        categories = {
            'Absorption': ['Caco2', 'Pgp', 'BBB_Martins', 'BBB_Adindo', 'OAT', 'OCT', 'drug_likeness'],
            'Distribution': ['VDss', 'FUP'],
            'Metabolism': ['CYP1A2', 'CYP2C19', 'CYP2C9', 'CYP2D6', 'CYP3A4', 'CYP2D6_2C9_3A4'],
            'Excretion': ['half_life', 'clearance', 'Vd'],
            'Toxicity': ['AMES', 'DILI', 'hERG', 'hERG2', 'skin_reaction', 'eye_corrosion', 'mutagenicity', 'tumorigenicity', 'irritation'],
            'Physicochemical Properties': ['logP', 'solubility', 'Lipinski_violation'],
            'Additional Properties': ['Caco2_Papp', 'Pgp_Papp', 'CYP1A2_IC50', 'CYP2C19_IC50', 'CYP2C9_IC50', 'CYP2D6_IC50', 'CYP3A4_IC50', 'LD50', 'hERG_IC50']
        }
        
        for category, props in categories.items():
            print(f"\n{category}:")
            print("-" * 70)
            
            for prop in props:
                if prop in preds and preds[prop] is not None:
                    value = preds[prop]
                    if prop in ['Caco2', 'Pgp', 'BBB_Martins', 'BBB_Adindo', 'OAT', 'OCT', 'drug_likeness', 'CYP1A2', 'CYP2C19', 'CYP2C9', 'CYP2D6', 'CYP3A4', 'CYP2D6_2C9_3A4', 'AMES', 'DILI', 'hERG', 'hERG2', 'skin_reaction', 'eye_corrosion', 'mutagenicity', 'tumorigenicity', 'irritation']:
                        # Classification properties
                        print(f"  {prop}: {value:.3f} (probability)")
                        # Identify relevant endpoints
                        if value > 0.7:
                            print(f"    ⚠️  RELEVANT ENDPOINT: {prop} - High probability")
                        elif value > 0.4:
                            print(f"    ⚠️  RELEVANT ENDPOINT: {prop} - Moderate probability")
                    else:
                        # Regression properties
                        print(f"  {prop}: {value:.3f}")
                else:
                    print(f"  {prop}: Not available")
        
        print("\n" + "="*70)
        print("\nIMPORTANT NOTES:")
        print("  • These are machine-learning predictions, not experimental measurements")
        print("  • Results should be validated with experimental data before regulatory decisions")
        print("  • High probability values (>0.7) indicate potential safety concerns")
        print("  • For MIE identification and AOP analysis, use the mie-identification skill")
        print("  • Properties marked with ⚠️ require special attention in drug development")
        print(f"{'='*70}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Predict ADMET properties using ADMET-AI."
    )
    
    parser.add_argument(
        '--smiles',
        nargs='+',
        help='SMILES string(s) to analyze',
        required=True
    )
    
    parser.add_argument(
        '--output',
        help='Output file path for detailed results (JSON)',
        default=None
    )
    
    args = parser.parse_args()
    
    # Predict ADMET properties
    print("Predicting ADMET properties...")
    results = predict_admet(args.smiles, args.output)
    
    # Print summary
    # Also ensure complete JSON output is available for other skills
    if not args.output:
        # If no output file specified, create a temporary JSON output
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(results, f, indent=2)
            temp_file = f.name
        print(f"\nComplete ADMET data also available at: {temp_file}")
        print("This file can be used by other skills and agents.")
    print_summary(results)


if __name__ == '__main__':
    main()