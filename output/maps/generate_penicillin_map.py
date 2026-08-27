import networkx as nx
import matplotlib.pyplot as plt
import math

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
    
    # MIE below
    if mie_nodes:
        y_pos = -1
        for node in mie_nodes:
            pos[node] = (0, y_pos)
            y_pos -= 1
    
    # KE nodes distributed vertically
    if ke_nodes:
        y_pos = -2 if not mie_nodes else min(pos.values(), key=lambda x: x[1])[1] - 1
        # For a linear path, keep them centered
        for node in ke_nodes:
            pos[node] = (0, y_pos)
            y_pos -= 1
            
    # AO at bottom
    if ao_nodes:
        y_pos = min(pos.values(), key=lambda x: x[1])[1] - 1
        for node in ao_nodes:
            pos[node] = (0, y_pos)
            
    return pos

def create_penicillin_aop_map():
    molecule_name = "Penicillin G"
    pathways = {
        'nodes': {
            'S1': ('Penicillin G', 'Stressor'),
            'MIE1': ('Covalent binding to host proteins\n(Haptenization)', 'MIE'),
            'KE1': ('Formation of Penicillin-Protein\nAdducts', 'KE'),
            'KE2': ('Antigen presentation and\nT-cell/B-cell activation', 'KE'),
            'KE3': ('IgE production and\nsensitization', 'KE'),
            'KE4': ('Mast cell degranulation', 'KE'),
            'AO1': ('Anaphylaxis / Skin Reaction', 'AO'),
        },
        'edges': [
            ('S1', 'MIE1', 'Induces'),
            ('MIE1', 'KE1', 'Triggers'),
            ('KE1', 'KE2', 'Leads to'),
            ('KE2', 'KE3', 'Triggers'),
            ('KE3', 'KE4', 'Causes'),
            ('KE4', 'AO1', 'Results in'),
        ],
        'colors': {
            'Stressor': 'gray',
            'MIE': 'red',
            'KE': 'blue',
            'AO': 'green',
        }
    }
    
    G = nx.DiGraph()
    for node_id, (label, node_type) in pathways['nodes'].items():
        G.add_node(node_id, label=label, type=node_type)
    
    for u, v, label in pathways['edges']:
        G.add_edge(u, v, label=label)
    
    pos = calculate_non_overlapping_positions(G)
    
    node_colors = [pathways['colors'][G.nodes[node]['type']] for node in G.nodes]
    
    plt.figure(figsize=(10, 12))
    
    # Use a consistent node size
    nx.draw_networkx_nodes(G, pos, node_size=5000, node_color=node_colors, 
                          edgecolors='black', linewidths=1.5, alpha=0.9)
    
    labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx_labels(G, pos, labels, font_size=9, font_weight='bold',
                           bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=1))
    
    nx.draw_networkx_edges(G, pos, width=2, alpha=0.6, edge_color='gray', 
                          arrowsize=20, connectionstyle='arc3,rad=0')
    
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8, 
                                bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=0.5))
    
    # Legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', label='Stressor', 
                  markerfacecolor='gray', markersize=12),
        plt.Line2D([0], [0], marker='o', color='w', label='MIE', 
                  markerfacecolor='red', markersize=12),
        plt.Line2D([0], [0], marker='o', color='w', label='KE', 
                  markerfacecolor='blue', markersize=12),
        plt.Line2D([0], [0], marker='o', color='w', label='AO', 
                  markerfacecolor='green', markersize=12)
    ]
    plt.legend(handles=legend_elements, loc='upper right')
    
    plt.title(f"Topological Map: {molecule_name} Hypersensitivity Pathway", 
             fontsize=14, pad=20, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    
    filename = "penicillin_g_aop_map.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Map saved as {filename}")
    return G

if __name__ == "__main__":
    create_penicillin_aop_map()
