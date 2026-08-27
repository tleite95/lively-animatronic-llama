import networkx as nx
import matplotlib.pyplot as plt
import math

def calculate_non_overlapping_positions(G):
    """
    Calculate positions for nodes to prevent overlaps.
    Uses a hierarchical layout with manual adjustments for complex graphs.
    """
    # Separate nodes by type
    mie_nodes = [node for node, data in G.nodes(data=True) if data['type'] == 'MIE']
    ke_nodes = [node for node, data in G.nodes(data=True) if data['type'] == 'KE']
    ao_nodes = [node for node, data in G.nodes(data=True) if data['type'] == 'AO']
    
    # Calculate positions based on node types
    pos = {}
    
    # Position MIE nodes at the top
    if mie_nodes:
        y_pos = 10
        for i, node in enumerate(mie_nodes):
            pos[node] = (i * 2, y_pos)
    
    # Position KE nodes in the middle
    if ke_nodes:
        # Determine levels based on distance from MIE
        levels = {}
        for node in ke_nodes:
            # Simple distance from MIE (assume MIEs are the source)
            dist = min([nx.shortest_path_length(G, source=m, target=node) for m in mie_nodes]) if mie_nodes else 1
            if dist not in levels:
                levels[dist] = []
            levels[dist].append(node)
        
        for dist, nodes_at_level in levels.items():
            y_pos = 10 - (dist * 2)
            for i, node in enumerate(nodes_at_level):
                pos[node] = (i * 2, y_pos)
    
    # Position AO nodes at the bottom
    if ao_nodes:
        y_pos = 2
        for i, node in enumerate(ao_nodes):
            pos[node] = (i * 2, y_pos)
    
    return pos

def create_general_aop_map(molecule_name, pathways):
    """
    Create a general topological map for any molecule's AOP pathways.
    """
    # Initialize Directed Graph
    G = nx.DiGraph()
    
    # Add nodes with labels and types
    for node_id, (label, node_type) in pathways['nodes'].items():
        G.add_node(node_id, label=label, type=node_type)
    
    # Add edges with labels
    for u, v, label in pathways['edges']:
        G.add_edge(u, v, label=label)
    
    # Calculate positions
    pos = calculate_non_overlapping_positions(G)
    
    # Color mapping for nodes
    node_colors = [pathways['colors'][G.nodes[node]['type']] for node in G.nodes]
    
    # Create figure
    plt.figure(figsize=(12, 14))
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=5000, node_color=node_colors, 
                          edgecolors='black', linewidths=1.5, alpha=0.9)
    
    # Draw labels
    labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight='bold',
                           bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=1))
    
    # Draw edges - straight vertical/diagonal lines
    nx.draw_networkx_edges(G, pos, width=2, alpha=0.6, edge_color='gray', 
                          arrowsize=20, connectionstyle='arc3,rad=0')
    
    # Draw edge labels
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=9, 
                                bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=0.5))
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', label='MIE', 
                  markerfacecolor=pathways['colors']['MIE'], markersize=12),
        plt.Line2D([0], [0], marker='o', color='w', label='KE', 
                  markerfacecolor=pathways['colors']['KE'], markersize=12),
        plt.Line2D([0], [0], marker='o', color='w', label='AO', 
                  markerfacecolor=pathways['colors']['AO'], markersize=12)
    ]
    plt.legend(handles=legend_elements, loc='upper right')
    
    plt.title(f"Topological Map: {molecule_name} Adverse Outcome Pathway\n(hERG Inhibition -> Cardiac Arrhythmia)", 
             fontsize=14, pad=20, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    
    filename = f"{molecule_name.lower().replace(' ', '_')}_aop_map.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Map saved as {filename}")
    return filename

# Data for Pinaverium hERG AOP
pinaverium_data = {
    'nodes': {
        'MIE1': ('MIE: Inhibition of hERG\nPotassium Channels', 'MIE'),
        'KE1': ('KE1: Delayed Ventricular\nRepolarization', 'KE'),
        'KE2': ('KE2: Prolonged Action\nPotential Duration (APD)', 'KE'),
        'KE3': ('KE3: Early After-Depolarizations\n(EADs)', 'KE'),
        'AO1': ('AO: Cardiac Arrhythmia\n(e.g., Torsades de Pointes)', 'AO'),
    },
    'edges': [
        ('MIE1', 'KE1', 'leads to'),
        ('KE1', 'KE2', 'causes'),
        ('KE2', 'KE3', 'triggers'),
        ('KE3', 'AO1', 'results in'),
    ],
    'colors': {
        'MIE': 'salmon',
        'KE': 'skyblue',
        'AO': 'darkred',
    }
}

if __name__ == "__main__":
    create_general_aop_map("Pinaverium", pinaverium_data)
