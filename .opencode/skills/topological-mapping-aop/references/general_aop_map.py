import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import math

# Standardized color scheme for all topological maps
STANDARD_COLOR_SCHEME = {
    "Stressor": "#FFD700",  # Gold
    "MIE": "#FF9090",      # Coral pink
    "KE": "#4DD7CE",       # Turquoise
    "AO": "#89221E"        # dark red
}

def create_general_aop_map(molecule_name, pathways):
    """
    Create a general topological map for any molecule's AOP pathways.
    
    Parameters:
    -----------
    molecule_name : str
        Name of the molecule for the title and filename.
    pathways : dict
        Dictionary containing pathway information with the following structure:
        {
            'nodes': {
                'Stressor1': ('Label for Stressor 1', 'Stressor'),
                'MIE1': ('Label for MIE 1', 'MIE'),
                'KE1': ('Label for KE 1', 'KE'),
                'KE2': ('Label for KE 2', 'KE'),
                'AO1': ('Label for AO 1', 'AO'),
                # Add more nodes as needed
            },
            'edges': [
                ('Stressor1', 'MIE1', 'Causes'),
                ('MIE1', 'KE1', 'Induces'),
                ('KE1', 'KE2', 'Triggers'),
                ('KE2', 'AO1', 'Leads to'),
                # Add more edges as needed
            ]
        }
    """
    
    # Initialize Directed Graph
    G = nx.DiGraph()
    
    # Add nodes with labels and types
    for node_id, (label, node_type) in pathways['nodes'].items():
        G.add_node(node_id, label=label, type=node_type)
    
    # Add edges with labels
    for u, v, label in pathways['edges']:
        G.add_edge(u, v, label=label)
    
    # Calculate positions to prevent overlaps
    pos = calculate_non_overlapping_positions(G)
    
    # Color mapping for nodes using standardized color scheme
    node_colors = [STANDARD_COLOR_SCHEME[G.nodes[node]['type']] for node in G.nodes]
    
    # Create figure with dynamic size based on number of nodes
    num_nodes = len(G.nodes)
    figsize = (max(8, num_nodes * 1.5), max(10, num_nodes * 2))
    plt.figure(figsize=figsize)
    
    # Draw nodes with enhanced styling
    node_sizes = [4000 + (i * 500) for i in range(len(G.nodes))]
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, 
                          edgecolors='black', linewidths=1.5, alpha=0.9)
    
    # Draw labels with enhanced styling
    labels = nx.get_node_attributes(G, 'label')
    # Ensure KE labels use short names by extracting the first part before any colon or comma
    display_labels = {}
    for node, label in labels.items():
        node_type = G.nodes[node]['type']
        if node_type == 'KE':
            # Extract short name (before colon, comma, or first space)
            short_name = label.split(':')[0].split(',')[0].split(' ')[0].strip()
            display_labels[node] = short_name
        else:
            display_labels[node] = label
    nx.draw_networkx_labels(G, pos, display_labels, font_size=10, font_weight='bold',
                           bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=1))
    
    # Draw edges with enhanced styling
    edge_colors = ['gray' for _ in G.edges]
    nx.draw_networkx_edges(G, pos, width=2, alpha=0.6, edge_color=edge_colors, 
                          arrowsize=20, connectionstyle='arc3,rad=0.1')
    
    # Draw edge labels with enhanced styling
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=9, 
                                bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=0.5))
    
    # Add legend with standardized colors
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
    plt.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.2, 1))
    
    # Add title and remove axes
    plt.title(f"Topological Map: {molecule_name} Adverse Outcome Pathway", 
             fontsize=14, pad=20, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    
    # Save the figure
    filename = f"{molecule_name.lower().replace(' ', '_')}_aop_map.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Map saved as {filename}")
    
    return G, pos

def calculate_non_overlapping_positions(G):
    """
    Calculate positions for nodes to prevent overlaps.
    Uses a hierarchical layout with manual adjustments for complex graphs.
    """
    # Separate nodes by type
    stressor_nodes = [node for node, data in G.nodes(data=True) if data['type'] == 'Stressor']
    mie_nodes = [node for node, data in G.nodes(data=True) if data['type'] == 'MIE']
    ke_nodes = [node for node, data in G.nodes(data=True) if data['type'] == 'KE']
    ao_nodes = [node for node, data in G.nodes(data=True) if data['type'] == 'AO']
    
    # Calculate positions based on node types
    pos = {}
    
    # Position stressor nodes at the very top
    if stressor_nodes:
        for node in stressor_nodes:
            pos[node] = (0, 0)
    
    # Position MIE nodes below stressor with fixed spacing
    if mie_nodes:
        y_pos = -3  # Fixed vertical spacing from stressor
        for node in mie_nodes:
            pos[node] = (0, y_pos)
    
    # Position KE nodes below MIE with fixed vertical spacing
    if ke_nodes:
        # Distribute KE nodes horizontally based on their connections
        ke_levels = {}
        for node in ke_nodes:
            # Count incoming edges to determine level
            incoming = len(list(G.predecessors(node)))
            if incoming not in ke_levels:
                ke_levels[incoming] = []
            ke_levels[incoming].append(node)
        
        # Calculate starting y position based on existing nodes
        if pos:
            y_pos = max(pos.values(), key=lambda x: x[1])[1] - 3  # Fixed vertical spacing
        else:
            y_pos = 0 - 3  # Start below y=0 if no nodes exist yet
        x_offset = 0
        
        for level in sorted(ke_levels.keys()):
            nodes_at_level = ke_levels[level]
            for i, node in enumerate(nodes_at_level):
                pos[node] = (x_offset, y_pos)
                x_offset += 2
            y_pos -= 3  # Fixed vertical spacing between levels
            x_offset = 0
    
    # Position AO nodes at the bottom with fixed spacing
    if ao_nodes:
        # Calculate starting y position based on existing nodes
        if pos:
            y_pos = min(pos.values(), key=lambda x: x[1])[1] - 3  # Fixed vertical spacing
        else:
            y_pos = 0 - 3  # Start below y=0 if no nodes exist yet
        x_offset = 0
        for node in ao_nodes:
            pos[node] = (x_offset, y_pos)
            x_offset += 2
    
    # Adjust positions to prevent overlaps
    pos = adjust_positions_to_prevent_overlaps(G, pos)
    
    return pos

def adjust_positions_to_prevent_overlaps(G, pos):
    """
    Adjust node positions to prevent overlaps.
    """
    adjusted_pos = pos.copy()
    
    # Get all node positions
    nodes = list(G.nodes())
    num_nodes = len(nodes)
    
    # Calculate minimum distance between nodes
    min_distance = 1.5
    
    # Iteratively adjust positions
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            node1 = nodes[i]
            node2 = nodes[j]
            
            # Calculate distance between nodes
            x1, y1 = adjusted_pos[node1]
            x2, y2 = adjusted_pos[node2]
            distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            
            # If nodes are too close, adjust their positions
            if distance < min_distance:
                # Calculate direction vector
                dx = x2 - x1
                dy = y2 - y1
                
                # Calculate adjustment
                adjustment = (min_distance - distance) / 2
                
                # Avoid division by zero - if nodes are at the same position,
                # move them apart vertically
                if distance > 0:
                    # Adjust positions based on direction
                    adjusted_pos[node1] = (x1 - dx * adjustment / distance, 
                                         y1 - dy * adjustment / distance)
                    adjusted_pos[node2] = (x2 + dx * adjustment / distance, 
                                         y2 + dy * adjustment / distance)
                else:
                    # Nodes are at the same position, move them apart vertically
                    adjusted_pos[node1] = (x1, y1 - min_distance / 2)
                    adjusted_pos[node2] = (x2, y2 + min_distance / 2)
    
    return adjusted_pos

def create_example_pathways():
    """
    Create example pathway data for demonstration.
    """
    return {
        'nodes': {
            'MIE1': ('Blockage of hERG Potassium Channels', 'MIE'),
            'MIE2': ('Inhibition of CYP3A4', 'MIE'),
            'KE1': ('Delayed Ventricular Repolarization\n(QT Prolongation)', 'KE'),
            'KE2': ('Triggered Activity\n(Early After-Depolarizations)', 'KE'),
            'KE3': ('Increased Drug Metabolism', 'KE'),
            'AO1': ('Ventricular Arrhythmia\n(Torsades de Pointes / SCD)', 'AO'),
            'AO2': ('Drug-Drug Interactions', 'AO')
        },
        'edges': [
            ('MIE1', 'KE1', 'Induces'),
            ('KE1', 'KE2', 'Triggers'),
            ('KE2', 'AO1', 'Leads to'),
            ('MIE2', 'KE3', 'Causes'),
            ('KE3', 'AO2', 'Results in'),
            ('MIE1', 'KE3', 'Also affects'),
            ('KE1', 'AO2', 'Contributes to')
        ],
        'colors': {
            'MIE': 'salmon',
            'KE': 'skyblue',
            'AO': 'darkred'
        }
    }

if __name__ == "__main__":
    # Example usage with a sample molecule
    molecule_name = "Example Molecule"
    pathways = create_example_pathways()
    
    # Create the AOP map
    G, pos = create_general_aop_map(molecule_name, pathways)
    
    print(f"Created AOP map for {molecule_name}")
    print(f"Graph has {len(G.nodes)} nodes and {len(G.edges)} edges")
