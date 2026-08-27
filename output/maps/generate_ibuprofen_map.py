import networkx as nx
import matplotlib.pyplot as plt
import math

# Standardized color scheme
STANDARD_COLOR_SCHEME = {
    "Stressor": "blue",
    "MIE": "yellow",
    "KE": "green",
    "AO": "red"
}

def calculate_non_overlapping_positions(G):
    # Separate nodes by type
    stressor_nodes = [node for node, data in G.nodes(data=True) if data['type'] == 'Stressor']
    mie_nodes = [node for node, data in G.nodes(data=True) if data['type'] == 'MIE']
    ke_nodes = [node for node, data in G.nodes(data=True) if data['type'] == 'KE']
    ao_nodes = [node for node, data in G.nodes(data=True) if data['type'] == 'AO']
    
    pos = {}
    # Stressor at top
    if stressor_nodes:
        for node in stressor_nodes:
            pos[node] = (0, 0)
    
    # MIEs below stressor
    if mie_nodes:
        y_pos = -2
        for i, node in enumerate(mie_nodes):
            pos[node] = (i * 4 - 2 if len(mie_nodes) > 1 else 0, y_pos)
    
    # KEs below MIEs
    if ke_nodes:
        # Simple layering for KEs
        # In this specific case, we have two distinct paths
        # Path 1: Prostaglandin -> Mucus -> Mucosal Vuln
        # Path 2: ROS -> Membrane Leak -> Hepatocyte Necrosis
        ke_levels = {
            'level1': [], # Immediate descendants of MIE
            'level2': [],
            'level3': []
        }
        
        for node in ke_nodes:
            # This is a simplification for the requested Ibuprofen pathways
            if 'Prostaglandin' in node or 'ROS' in node:
                ke_levels['level1'].append(node)
            elif 'Mucus' in node or 'Membrane' in node:
                ke_levels['level2'].append(node)
            else:
                ke_levels['level3'].append(node)
        
        y_offset = -4
        for level in ['level1', 'level2', 'level3']:
            nodes = ke_levels[level]
            for i, node in enumerate(nodes):
                # Offset x based on which path it belongs to
                # Path 1 (Gastric) on left, Path 2 (DILI) on right
                x_pos = -4 if 'Prostaglandin' in node or 'Mucus' in node or 'Mucosal' in node else 4
                if 'ROS' in node or 'Membrane' in node or 'Hepatocyte' in node:
                    x_pos = 4
                pos[node] = (x_pos, y_offset)
            y_offset -= 2
            
    # AOs at the bottom
    if ao_nodes:
        y_pos = -12
        for i, node in enumerate(ao_nodes):
            # Path 1 (Gastric) left, Path 2 (DILI) right
            x_pos = -4 if 'Gastric' in node else 4
            pos[node] = (x_pos, y_pos)
            
    return pos

def create_ibuprofen_map():
    molecule_name = "Ibuprofen"
    
    pathways = {
        'nodes': {
            'Stressor': ('Ibuprofen', 'Stressor'),
            'MIE_COX': ('COX Inhibition', 'MIE'),
            'MIE_Mito': ('Mitochondrial Dysfunction', 'MIE'),
            'KE_Pros': ('Prostaglandin Depletion', 'KE'),
            'KE_Mucus': ('Mucus Reduction', 'KE'),
            'KE_Vuln': ('Mucosal Vulnerability', 'KE'),
            'AO_Gastric': ('Gastric Mucosal Injury', 'AO'),
            'KE_ROS': ('ROS Generation', 'KE'),
            'KE_Leak': ('Membrane Leakage', 'KE'),
            'KE_Necro': ('Hepatocyte Necrosis', 'KE'),
            'AO_DILI': ('Drug-Induced Liver Injury', 'AO'),
        },
        'edges': [
            ('Stressor', 'MIE_COX', 'Induces'),
            ('MIE_COX', 'KE_Pros', 'Leads to'),
            ('KE_Pros', 'KE_Mucus', 'Triggers'),
            ('KE_Mucus', 'KE_Vuln', 'Causes'),
            ('KE_Vuln', 'AO_Gastric', 'Results in'),
            ('Stressor', 'MIE_Mito', 'Induces'),
            ('MIE_Mito', 'KE_ROS', 'Leads to'),
            ('KE_ROS', 'KE_Leak', 'Triggers'),
            ('KE_Leak', 'KE_Necro', 'Causes'),
            ('KE_Necro', 'AO_DILI', 'Results in'),
        ]
    }
    
    G = nx.DiGraph()
    for node_id, (label, node_type) in pathways['nodes'].items():
        G.add_node(node_id, label=label, type=node_type)
    for u, v, label in pathways['edges']:
        G.add_edge(u, v, label=label)
        
    pos = calculate_non_overlapping_positions(G)
    
    # Use spring_layout for "force-directed" feel but maintain the general structure
    # Actually, for AOPs, a hybrid or structured force-directed is better.
    # Let's use the manual pos as a seed for spring_layout
    pos_fd = nx.spring_layout(G, pos=pos, fixed=None, k=2, iterations=50)
    
    node_colors = [STANDARD_COLOR_SCHEME[G.nodes[node]['type']] for node in G.nodes]
    
    plt.figure(figsize=(12, 10))
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos_fd, node_size=3000, node_color=node_colors, 
                           edgecolors='black', linewidths=1.5, alpha=0.9)
    
    # Draw labels
    labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx_labels(G, pos_fd, labels, font_size=10, font_weight='bold',
                           bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=1))
    
    # Draw edges
    nx.draw_networkx_edges(G, pos_fd, width=2, alpha=0.6, edge_color='gray', 
                           arrowsize=20, connectionstyle='arc3,rad=0.1')
    
    # Draw edge labels
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos_fd, edge_labels, font_size=8, 
                                 bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=0.5))
    
    # Legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', label='Stressor', 
                  markerfacecolor=STANDARD_COLOR_SCHEME['Stressor'], markersize=12),
        plt.Line2D([0], [0], marker='o', color='w', label='MIE', 
                  markerfacecolor=STANDARD_COLOR_SCHEME['MIE'], markersize=12),
        plt.Line2D([0], [0], marker='o', color='w', label='KE', 
                  markerfacecolor=STANDARD_COLOR_SCHEME['KE'], markersize=12),
        plt.Line2D([0], [0], marker='o', color='w', label='AO', 
                  markerfacecolor=STANDARD_COLOR_SCHEME['AO'], markersize=12)
    ]
    plt.legend(handles=legend_elements, loc='upper right')
    
    plt.title(f"Enhanced Topological Map: {molecule_name} Adverse Outcome Pathways", 
              fontsize=14, pad=20, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    
    filename = "ibuprofen_aop_map.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Map saved as {filename}")
    return G

if __name__ == "__main__":
    create_ibuprofen_map()
