---
name: topological-mapping-aop
description: Tools and methods for creating topological maps of Adverse Outcome Pathway (AOP) networks
---

# Topological Mapping of AOP Pathways

## Description
This skill provides comprehensive tools and methods for creating topological maps of Adverse Outcome Pathway (AOP) networks. It enables visualization and analysis of complex biological pathways, identifying key nodes, critical pathways, and potential intervention points. This expanded version includes advanced features for temporal analysis, robustness assessment, and interactive visualization. ALWAYS use enhanced visualization capabilities to ensure maps are readable, well-formatted, and accessible.

## Capabilities
- **Pathway Analysis**: Analyze AOP networks to identify key biological nodes and pathways
- **Topological Mapping**: Create visual representations of AOP networks showing connections between molecular initiating events (MIEs), key events (KEs), and adverse outcomes (AOs)
- **Critical Path Identification**: Identify critical pathways that significantly contribute to adverse outcomes
- **Intervention Point Analysis**: Determine optimal intervention points to disrupt harmful pathways
- **Network Metrics**: Calculate network metrics such as betweenness centrality, degree centrality, and other topological properties

## **Every Map should include:**
- **Clear labeling of nodes and edges with relevant biological information (e.g., KE1, KE2, AO1)**
- **All maps should follow formatting in the reference implementation**
- Color coding for different types of nodes (MIEs, KEs, AOs) and edges (activation, inhibition)
- Edge thickness proportional to confidence scores or interaction strength
- Labels for confidence and KE, MIE, AO, and Stressor.
- NO overlapping text or nodes; use text wrapping and node clustering to reduce clutter
- Use of force-directed or hierarchical layouts for better readability


## Use Cases
- Understanding complex biological pathways and their interactions
- Identifying key nodes that play critical roles in disease progression
- Visualizing AOP networks for research and presentation purposes
- Studying temporal dynamics of pathway activation and progression
- Creating interactive visualizations for educational and research purposes
- Integrating with AOP construction workflows to validate pathway structure
- Identifying critical pathways in AOPs constructed by other agents
- Finding intervention points in AOPs for drug development
- Validating biological plausibility of constructed AOPs through network analysis

## Implementation Details

### Core Components
1. **Graph Representation**: AOP pathways are represented as directed graphs where:
    - Nodes represent biological entities (genes, proteins, metabolites, etc.)
    - **Node Categories**: Nodes should be categorized by AOP level (e.g., Stressor, MIE, KE, AO) for visual grouping.
    - Edges represent relationships or interactions between entities
    - Edge weights represent confidence scores or interaction strengths
    - **Modulating Nodes**: The graph should support non-linear nodes that act as "Modulators" (e.g., Genetic Polymorphisms, Drug-Drug Interactions, Electrolyte Imbalances) which influence the strength or probability of an edge.
    - Temporal information can be incorporated for dynamic analysis
    - **ALWAYS** label edges and nodes with relevant biological information for clarity and KE1, KE2, AO1, etc.
    - **Layout Constraint**: All connections must go straight down vertically. Pathways only split horizontally when they diverge into multiple branches. **Uniform vertical spacing of 3 units between levels ensures all edges have consistent length.**

### Reference Implementation
The skill includes a reference implementation for creating general AOP maps. See the reference files in the `references/` directory for the complete implementation:

- `general_aop_map.py`: Main implementation for creating general AOP maps
- `combined_map_generation_utils.py`: Utility functions for standardized layouts and visualization
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
                'MIE1': ('Label for MIE 1', 'MIE'),
                'KE1': ('Label for KE 1', 'KE'),
                'KE2': ('Label for KE 2', 'KE'),
                'AO1': ('Label for AO 1', 'AO'),
                # Add more nodes as needed
            },
            'edges': [
                ('MIE1', 'KE1', 'Induces'),
                ('KE1', 'KE2', 'Triggers'),
                ('KE2', 'AO1', 'Leads to'),
                # Add more edges as needed
            ],
            'colors': {
                'MIE': 'salmon',
                'KE': 'skyblue',
                'AO': 'darkred',
                # Add more node types and colors as needed
            }
        }
    """
    
    # Initialize Directed Graph
    G = nx.DiGraph()
    
    # Add nodes with labels and types, ensuring top-down format
    # First add nodes in order: Stressor → MIE → KE → AO
    node_order = {}
    for node_id, (label, node_type) in pathways['nodes'].items():
        G.add_node(node_id, label=label, type=node_type)
        # Assign order based on node type to ensure top-down layout
        if node_type == 'Stressor':
            node_order[node_id] = 0
        elif node_type == 'MIE':
            node_order[node_id] = 1
        elif node_type == 'KE':
            node_order[node_id] = 2
        elif node_type == 'AO':
            node_order[node_id] = 3
        else:
            node_order[node_id] = 4  # Default for other types
    
    # Add edges with labels
    for u, v, label in pathways['edges']:
        G.add_edge(u, v, label=label)
    
    # Calculate positions to prevent overlaps
    pos = calculate_non_overlapping_positions(G)
    
    # Color mapping for nodes
    node_colors = [pathways['colors'][G.nodes[node]['type']] for node in G.nodes]
    
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
    nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight='bold',
                           bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=1))
    
    # Draw edges with enhanced styling
    edge_colors = ['gray' for _ in G.edges]
    nx.draw_networkx_edges(G, pos, width=2, alpha=0.6, edge_color=edge_colors, 
                          arrowsize=20, connectionstyle='arc3,rad=0.1')
    
    # Draw edge labels with enhanced styling
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=9, 
                                bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=0.5),
                                label_style={'connectionstyle': 'arc3,rad=0.1'})
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', label='MIE', 
                  markerfacecolor=pathways['colors']['MIE'], markersize=12),
        plt.Line2D([0], [0], marker='o', color='w', label='KE', 
                  markerfacecolor=pathways['colors']['KE'], markersize=12),
        plt.Line2D([0], [0], marker='o', color='w', label='AO', 
                  markerfacecolor=pathways['colors']['AO'], markersize=12)
    ]
    plt.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.2, 1))
    
    # Add title and remove axes
    plt.title(f"Topological Map: {molecule_name} Adverse Outcome Pathway", 
             fontsize=14, pad=20, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    
    # Save the figure
    # Check if OUTPUT_PATH is provided in the environment or as a parameter
    output_path = os.environ.get("OUTPUT_PATH", None)
    if output_path:
        filename = output_path
    else:
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
    
    # Position MIE nodes below stressor
    if mie_nodes:
        y_pos = -1
        for node in mie_nodes:
            pos[node] = (0, y_pos)
            y_pos -= 1
    
    # Position KE nodes below MIE
    if ke_nodes:
        # Distribute KE nodes horizontally based on their connections
        ke_levels = {}
        for node in ke_nodes:
            # Count incoming edges to determine level
            incoming = len(list(G.predecessors(node)))
            if incoming not in ke_levels:
                ke_levels[incoming] = []
            ke_levels[incoming].append(node)
        
        y_pos = max(pos.values(), key=lambda x: x[1])[1] - 1.5
        x_offset = 0
        
        for level in sorted(ke_levels.keys()):
            nodes_at_level = ke_levels[level]
            for i, node in enumerate(nodes_at_level):
                pos[node] = (x_offset, y_pos)
                x_offset += 2
            y_pos -= 1.5
            x_offset = 0
    
    # Position AO nodes at the bottom
    if ao_nodes:
        y_pos = min(pos.values(), key=lambda x: x[1])[1] - 1.5
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
                
                # Adjust positions
                adjusted_pos[node1] = (x1 - dx * adjustment / distance, 
                                     y1 - dy * adjustment / distance)
                adjusted_pos[node2] = (x2 + dx * adjustment / distance, 
                                     y2 + dy * adjustment / distance)
    
See the reference files in the `references/` directory for the complete implementation.
```

2. **Algorithmic Analysis**:
   - Path finding algorithms to identify critical pathways
   - Centrality measures to identify key nodes
   - Network flow analysis to understand information propagation
   - Community detection to identify modular structures
   - Temporal analysis algorithms for dynamic networks
   - Robustness assessment algorithms for network resilience

3. **Visualization**:
    - Use text wrapping and node clustering to reduce clutter and ensure no information is lost in complex networks
   - Force-directed layouts for network visualization
   - Hierarchical layouts for pathway representation
   - Interactive visualizations with zoom and pan capabilities
   - Temporal visualization for dynamic networks

### Key Functions
- `create_topological_map(pathway_data)`: Create a topological map from pathway data
- `create_general_aop_map(molecule_name, pathways)`: Create a general topological map using the reference implementation
- `analyze_critical_paths(map)`: Identify critical pathways in the network
- `find_intervention_points(map)`: Find optimal intervention points
- `calculate_network_metrics(map)`: Calculate various network metrics
- `visualize_map(map, config=None)`: Generate visual representations of the map with customizable styling
- `visualize_enhanced(map, config=None)`: Create enhanced visualizations with advanced formatting options
- `visualize_interactive(map, config=None)`: Create interactive network visualizations with Plotly
- `visualize_temporal(map, time_series_data, config=None)`: Generate temporal visualizations and animations
- `visualize_3d(map, config=None)`: Create 3D visualizations for complex networks
- `analyze_temporal_dynamics(map, time_series_data)`: Analyze temporal evolution of the network
- `find_robustness_metrics(map)`: Assess network resilience to perturbations
- `validate_aop_structure(map)`: Validate AOP biological plausibility through network analysis
- `compare_networks(map1, map2)`: Compare two AOP networks for similarity
- `create_comprehensive_visualization(map, critical_paths, intervention_points)`: Create integrated visualization
- `identify_subnetworks(map)`: Identify modular components in complex networks
- `assess_robustness_with_sampling(map, sample_size)`: Efficient robustness assessment for large networks
- `calculate_non_overlapping_positions(G)`: Calculate positions for nodes to prevent overlaps
- `adjust_positions_to_prevent_overlaps(G, pos)`: Adjust node positions to prevent overlaps

#### Visualization Configuration Options

```python
# Comprehensive visualization configuration
vis_config = {
    # Layout options
    'layout': 'hierarchical',
    'layout_kwargs': {'scale': 2.0, 'center': (0, 0)},
    
    # Node styling
    'node_size_scale': 1000,  # Base size for nodes
    'node_color_by': 'type', # 'type', 'degree', 'betweenness', 'closeness'
    'node_color_scheme': 'colorblind_friendly',  # 'viridis', 'plasma', 'cividis'
    'node_border_width': 1.5,
    'node_border_color': 'black',
    'node_alpha': 0.9,
    
    # Edge styling
    'edge_linewidth_scale': 2,  # Base edge thickness
    'edge_linewidth_min': 0.5,  # Minimum edge thickness
    'edge_linewidth_max': 5.0,  # Maximum edge thickness
    'edge_color_by': 'weight',  # 'type', 'weight', 'confidence'
    'edge_color_scheme': 'RdYlGn',  # Green-Red gradient
    'edge_alpha': 0.4,          # Edge transparency
    'edge_style': 'solid',      # 'solid', 'dashed', 'dotted'
    
    # Label options
    'show_labels': True,
    'label_fontsize': 10,
    'label_fontweight': 'normal',
    'label_color': 'black',
    'label_offset': 0.05,
    
    # Figure options
    'figsize': (16, 12),       # Figure dimensions
    'dpi': 300,                # Resolution
    'facecolor': 'white',      # Background color
    'edgecolor': 'white',      # Figure edge color
    
    # Title and legend
    'title': 'AOP Network Topology',
    'title_fontsize': 16,
    'title_fontweight': 'bold',
    'with_legend': True,
    'legend_fontsize': 9,
    'legend_loc': 'upper right',
    
    # Color mapping
    'color_mapping': {
        'MIE': 'red',
        'KE': 'blue',
        'AO': 'darkred',
        'intermediate': 'lightblue'
    },
    
}

# Generate enhanced visualization
fig = topological_map.visualize_enhanced(config=vis_config)
```

#### Layout Algorithms

1. **Force-Directed**: Natural organization based on physical simulation
   - Best for: Small to medium networks with natural clustering
   - Parameters: `scale`, `k` (repulsion strength), `iterations`

2. **Hierarchical**: Organizes nodes by temporal progression
   - Best for: Pathways with clear temporal ordering
   - Parameters: `level_separation`, `node_distance`, `rank_separation`

3. **Circular**: Nodes arranged in a circle
   - Best for: Cyclic pathways and feedback loops
   - Parameters: `scale`, `rotation`

#### Color Schemes

- **Colorblind-Friendly**: 'viridis', 'plasma', 'cividis', 'inferno'
- **High Contrast**: 'Set1', 'Set2', 'Set3'
- **Sequential**: 'Blues', 'Reds', 'Greens', 'Purples', 'Oranges'

#### Output Formats
- **Static Images**: PNG

#### Accessibility Features

- **Colorblind Mode**: Automatic detection and alternative palettes
- **High Contrast Mode**: Enhanced visibility for all elements
- **Screen Reader Support**: Alternative text descriptions
- **Responsive Design**: Adapts to different display sizes

#### Advanced Features

- **Edge Bundling**: Reduces clutter in dense networks
- **Node Clustering**: Groups related nodes automatically
- **Subnetwork Extraction**: Focus on specific pathways
- **Comparative Visualization**: Side-by-side network comparison
- **Interactive Tooltips**: Detailed information on hover

### Layout Constraints

**IMPORTANT**: All topological maps MUST follow these layout constraints:

1. **Top-Down Format**: AO nodes must be at the bottom, stressor nodes at the top
2. **Straight Vertical Lines**: All connections must go straight down vertically
3. **Horizontal Splitting Only**: Pathways only split horizontally when they diverge into multiple branches
4. **No Overlapping Lines**: Lines should not cross or overlap unless absolutely necessary for complex branching
5. **Consistent Spacing**: Equal vertical spacing between levels (3 units between each level)
6. **Uniform Edge Lengths**: All edges connecting nodes must be of uniform length to maintain visual consistency

### Visualization Improvements

The topological mapping skill provides enhanced visualization capabilities to make complex AOP networks more readable and better formatted:

#### 1. **Enhanced Layout Algorithms**
- **Top-Down Hierarchical Layout**: Organizes nodes by temporal progression (Stressor → MIE → KE → AO) with straight vertical connections. Pathways only split horizontally when they diverge into multiple branches. **Uniform vertical spacing of 3 units between each level ensures consistent edge lengths.**
- **Force-Directed Layout**: Optimized for balanced node distribution, reducing overlaps
- **Circular Layout**: Useful for cyclic pathways and feedback loops

#### 2. **Improved Node and Edge Styling**
- **Color Coding**: 
  - Molecular Initiating Events (MIEs): Red
  - Key Events (KEs): Blue
  - Adverse Outcomes (AOs): Dark Red
  - Intermediate nodes: Light Blue
- **Edge Thickness**: Weighted by confidence scores or interaction strength
- **Edge Colors**: Green for activation, Red for inhibition, Gray for unknown

#### 3. **Interactive Features**
- **Edge Filtering**: Toggle edges by weight/confidence threshold
- **Dynamic Zooming**: Smooth zoom and pan capabilities

#### 4. **Accessibility Enhancements**
- **Colorblind-Friendly Palettes**: Multiple color schemes for accessibility
- **Clear Labels**: Readable font sizes (10pt for nodes, 8pt for edge labels)
- **High Contrast**: Ensures visibility against backgrounds
- **Legend System**: Comprehensive legend explaining all visual elements

## Example Usage

### Basic Usage

```python
# Load pathway data
pathway_data = load_aop_data("aspirin_aop.json")

# Create topological map
topological_map = create_topological_map(pathway_data)

# Analyze critical pathways
critical_paths = analyze_critical_paths(topological_map)

# Find intervention points
intervention_points = find_intervention_points(topological_map)

# Visualize the map
visualize_map(topological_map)

# Analyze temporal dynamics (if time series data available)
time_series = load_time_series_data("aspirin_timeline.csv")
temporal_results = topological_map.analyze_temporal_dynamics(time_series)

# Assess network robustness
robustness_metrics = topological_map.find_robustness_metrics()
```

### Integration with AOP Construction

```python
# Integration with aop-constructor workflow
import os
from aop_constructor import AOPConstructor
from topological_mapping import TopologicalAnalyzer

# Step 1: Construct AOP using aop-constructor
aop_constructor = AOPConstructor()
molecule = "CC(=O)OC1=CC=CC=C1C(=O)O"  # Aspirin
result = aop_constructor.analyze_molecule(molecule)

# Step 2: Get AOP data from the result
aop_data = result.aop_structure

# Step 3: Create topological analyzer
topological_analyzer = TopologicalAnalyzer()

# Step 4: Create topological map from AOP data
topological_map = topological_analyzer.create_topological_map(aop_data)

# Step 5: Analyze the network
critical_paths = topological_analyzer.analyze_critical_paths(topological_map)
intervention_points = topological_analyzer.find_intervention_points(topological_map)
metrics = topological_analyzer.calculate_network_metrics(topological_map)

# Step 6: Validate AOP structure
validation = topological_analyzer.validate_aop_structure(topological_map)
if validation.is_valid:
    print("AOP structure is biologically plausible")
else:
    print(f"Validation issues: {validation.issues}")

# Step 7: Generate comprehensive visualization
visualization = topological_analyzer.create_comprehensive_visualization(
    topological_map,
    critical_paths,
    intervention_points
)
visualization.save("integrated_aop_analysis.png")
```

## Dependencies
- Python 3.8+
- NetworkX for graph operations
- Matplotlib or Plotly for visualization
- NumPy for numerical operations
- Pandas for data manipulation
- scikit-learn for machine learning algorithms (temporal analysis)
- RDKit for chemical structure handling (optional)

## Performance Considerations
- For large networks, consider using efficient graph algorithms
- Implement caching for frequently accessed network metrics
- Use incremental updates for dynamic networks
- Consider parallel processing for computationally intensive operations