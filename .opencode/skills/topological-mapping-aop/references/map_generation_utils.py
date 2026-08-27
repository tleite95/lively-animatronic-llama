"""
Utility functions for generating consistent topological maps with standardized 
color schemes and hierarchical layouts.

LAYOUT CONSTRAINTS:
1. Top-Down Format: AO nodes must be at the bottom, stressor nodes at the top
2. Straight Vertical Lines: All connections must go straight down vertically
3. Horizontal Splitting Only: Pathways only split horizontally when they diverge into multiple branches
4. No Overlapping Lines: Lines should not cross or overlap unless absolutely necessary for complex branching
5. Consistent Spacing: Equal vertical spacing between levels
"""

import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional

# Standardized color scheme for all topological maps
STANDARD_COLOR_SCHEME = {
    "Stressor": "#FFD700",  # Gold
    "MIE": "#FF9090",      # Coral pink
    "KE": "#4DD7CE",       # Turquoise
    "AO": "#89221E"        # dark red
}

def create_standardized_layout(G: nx.DiGraph) -> Dict:
    """
    Create a top-down hierarchical layout for AOP maps with straight vertical connections.
    
    Args:
        G: NetworkX DiGraph containing nodes with 'type' attribute
        
    Returns:
        Dictionary of node positions
    """
    # Separate nodes by type
    stressor_nodes = [node for node, data in G.nodes(data=True) if data['type'] == 'Stressor']
    mie_nodes = [node for node, data in G.nodes(data=True) if data['type'] == 'MIE']
    ke_nodes = [node for node, data in G.nodes(data=True) if data['type'] == 'KE']
    ao_nodes = [node for node, data in G.nodes(data=True) if data['type'] == 'AO']
    
    pos = {}
    y_pos = 0
    x_pos = 0
    
    # Place stressor at the top (centered)
    if stressor_nodes:
        for node in stressor_nodes:
            pos[node] = (x_pos, y_pos)
        y_pos -= 3  # Fixed vertical spacing
    
    # Place MIE nodes below stressor (centered)
    if mie_nodes:
        for i, node in enumerate(mie_nodes):
            pos[node] = (x_pos, y_pos)
        y_pos -= 3
    
    # Place KE nodes below MIE with straight vertical connections
    if ke_nodes:
        # Organize KE nodes by their level in the hierarchy
        # Level 0: directly connected to MIE
        # Level 1: connected to Level 0 KEs
        # etc.
        
        # First, identify the root nodes (connected to MIE or stressor)
        root_kes = []
        for node in ke_nodes:
            predecessors = list(G.predecessors(node))
            # Check if any predecessor is MIE or stressor
            is_root = any(
                G.nodes[p]['type'] in ['MIE', 'Stressor'] 
                for p in predecessors
            )
            if is_root:
                root_kes.append(node)
        
        # Place root KE nodes directly below their predecessors
        if root_kes:
            # Position root KEs below MIE nodes
            for i, node in enumerate(root_kes):
                pos[node] = (x_pos + i * 2, y_pos)
            y_pos -= 3  # Fixed vertical spacing
        
        # Process remaining KE nodes level by level
        processed_nodes = set(stressor_nodes + mie_nodes + root_kes)
        current_level_nodes = root_kes.copy()
        
        while current_level_nodes:
            next_level_nodes = []
            # Find all KE nodes that are children of current level nodes
            for node in ke_nodes:
                if node in processed_nodes:
                    continue
                predecessors = list(G.predecessors(node))
                # Check if any predecessor is in current level
                if any(p in current_level_nodes for p in predecessors):
                    next_level_nodes.append(node)
            
            if next_level_nodes:
                # Position these nodes below their parents
                for node in next_level_nodes:
                    predecessors = list(G.predecessors(node))
                    # Use the x position of the first predecessor
                    parent_x = pos[predecessors[0]][0]
                    pos[node] = (parent_x, y_pos)
                processed_nodes.update(next_level_nodes)
                current_level_nodes = next_level_nodes
                y_pos -= 3  # Fixed vertical spacing
    
    # Place AO nodes at the bottom (centered)
    if ao_nodes:
        for i, node in enumerate(ao_nodes):
            pos[node] = (x_pos + i * 2, y_pos)
    
    return pos

def create_hierarchical_layout(G: nx.DiGraph) -> Dict:
    """
    Alias for create_standardized_layout to maintain backward compatibility.
    """
    return create_standardized_layout(G)

def draw_edges_with_smart_curving(G: nx.DiGraph, pos: Dict, **kwargs):
    """
    Draw edges with straight vertical lines by default, only curving when paths split.
    
    Args:
        G: NetworkX DiGraph
        pos: Node positions dictionary
        **kwargs: Additional arguments to pass to nx.draw_networkx_edges
    """
    # Check if any node has multiple successors (path splitting)
    has_splitting = any(len(list(G.successors(node))) > 1 for node in G.nodes())
    
    if has_splitting:
        # Use curved edges when paths split
        default_kwargs = {'connectionstyle': 'arc3,rad=0.1'}
    else:
        # Use straight vertical edges when no splitting occurs
        default_kwargs = {'connectionstyle': 'arc3,rad=0.0'}
    
    # Merge default kwargs with user-provided kwargs
    all_kwargs = {**default_kwargs, **kwargs}
    nx.draw_networkx_edges(G, pos, **all_kwargs)

def generate_standardized_map(
    G: nx.DiGraph,
    title: str = "Topological Map of AOP Network",
    figsize: Tuple[int, int] = (12, 10),
    output_path: Optional[str] = None
) -> str:
    """
    Generate a standardized topological map with consistent color scheme and layout.
    
    Args:
        G: NetworkX DiGraph with nodes having 'type' and 'label' attributes
        title: Title for the map
        figsize: Figure size
        output_path: Path to save the map (default: generate filename)
        
    Returns:
        Path to the saved map image
    """
    # Get node colors using standard scheme
    node_colors = [STANDARD_COLOR_SCHEME[G.nodes[node]['type']] for node in G.nodes()]
    
    # Create layout
    pos = create_standardized_layout(G)
    
    # Create figure
    plt.figure(figsize=figsize)
    
    # Draw nodes
    node_sizes = [3000 for _ in G.nodes()]
    nx.draw_networkx_nodes(
        G, pos, 
        node_size=node_sizes, 
        node_color=node_colors, 
        edgecolors='black', 
        linewidths=1.5, 
        alpha=0.9
    )
    
    # Draw labels
    # Ensure KE labels use short names by extracting the first part before any colon or comma
    labels = {}
    for node in G.nodes():
        label = G.nodes[node]['label']
        node_type = G.nodes[node]['type']
        if node_type == 'KE':
            # Extract short name (before colon, comma, or first space)
            short_name = label.split(':')[0].split(',')[0].split(' ')[0].strip()
            labels[node] = short_name
        else:
            labels[node] = label
    
    nx.draw_networkx_labels(
        G, pos, 
        labels=labels, 
        font_size=10, 
        font_weight='bold',
        bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=1)
    )
    
    # Draw edges with smart curving
    draw_edges_with_smart_curving(
        G, pos, 
        width=2, 
        alpha=0.6, 
        edge_color='gray', 
        arrowstyle='->', 
        arrowsize=20
    )
    
    # Create legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=STANDARD_COLOR_SCHEME['Stressor'], edgecolor='black', label='Stressor'),
        Patch(facecolor=STANDARD_COLOR_SCHEME['MIE'], edgecolor='black', label='MIE'),
        Patch(facecolor=STANDARD_COLOR_SCHEME['KE'], edgecolor='black', label='Key Event (KE)'),
        Patch(facecolor=STANDARD_COLOR_SCHEME['AO'], edgecolor='black', label='Adverse Outcome (AO)')
    ]
    plt.legend(handles=legend_elements, loc='upper right', title="Node Types")
    
    # Add title and save
    plt.title(title, fontsize=15, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    
    # Determine output path
    if output_path is None:
        # Generate from title
        safe_title = title.replace(' ', '_').replace(':', '').lower()
        output_path = f"{safe_title}.png"
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_path