import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from workflows.map_generation_utils import generate_standardized_map, convert_legacy_map_to_standard

def generate_daridorexant_aop_maps():
    # Define the AOP data
    aops = {
        "Cardiotoxicity": {
            "nodes": [
                ("Daridorexant", "Stressor"),
                ("hERG Potassium Channel Inhibition", "MIE"),
                ("Delayed Ventricular Repolarization", "KE"),
                ("QT Interval Prolongation", "KE"),
                ("Torsades de Pointes / Ventricular Arrhythmia", "AO")
            ],
            "edges": [
                ("Daridorexant", "hERG Potassium Channel Inhibition"),
                ("hERG Potassium Channel Inhibition", "Delayed Ventricular Repolarization"),
                ("Delayed Ventricular Repolarization", "QT Interval Prolongation"),
                ("QT Interval Prolongation", "Torsades de Pointes / Ventricular Arrhythmia")
            ]
        },
        "Hepatotoxicity": {
            "nodes": [
                ("Daridorexant", "Stressor"),
                ("CYP-Mediated Bioactivation", "MIE"),
                ("Formation of Reactive Metabolites / ROS", "KE"),
                ("Mitochondrial Membrane Depolarization", "KE"),
                ("Hepatocyte Necrosis/Apoptosis", "KE"),
                ("Liver Injury / Steatosis", "AO")
            ],
            "edges": [
                ("Daridorexant", "CYP-Mediated Bioactivation"),
                ("CYP-Mediated Bioactivation", "Formation of Reactive Metabolites / ROS"),
                ("Formation of Reactive Metabolites / ROS", "Mitochondrial Membrane Depolarization"),
                ("Mitochondrial Membrane Depolarization", "Hepatocyte Necrosis/Apoptosis"),
                ("Hepatocyte Necrosis/Apoptosis", "Liver Injury / Steatosis")
            ]
        },
        "Endocrine Disruption": {
            "nodes": [
                ("Daridorexant", "Stressor"),
                ("CYP19A1 (Aromatase) Inhibition", "MIE"),
                ("Decreased Conversion of Androgens to Estrogens", "KE"),
                ("Reduced Systemic Estrogen Levels", "KE"),
                ("Impaired Reproductive Function / Bone Density Loss", "AO")
            ],
            "edges": [
                ("Daridorexant", "CYP19A1 (Aromatase) Inhibition"),
                ("CYP19A1 (Aromatase) Inhibition", "Decreased Conversion of Androgens to Estrogens"),
                ("Decreased Conversion of Androgens to Estrogens", "Reduced Systemic Estrogen Levels"),
                ("Reduced Systemic Estrogen Levels", "Impaired Reproductive Function / Bone Density Loss")
            ]
        }
    }

    # Create a single graph combining all AOPs for a global topological map
    G = nx.DiGraph()
    
    for aop_name, data in aops.items():
        for node, ntype in data["nodes"]:
            G.add_node(node, label=node, type=ntype)
        G.add_edges_from(data["edges"])
    
    # Convert to standard format and generate map
    standard_G = convert_legacy_map_to_standard(G)
    output_path = generate_standardized_map(
        standard_G,
        title="Topological Map of Daridorexant Adverse Outcome Pathways (AOPs)",
        figsize=(16, 12)
    )
    return output_path

if __name__ == "__main__":
    path = generate_daridorexant_aop_maps()
    print(f"Map saved to: {path}")
