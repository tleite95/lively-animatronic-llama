# AOP Workflow Architecture

## Overview

The AOP (Adverse Outcome Pathway) prediction workflow is organized as a modular, LangGraph-based orchestration system. The architecture follows a clear separation of concerns with workflow.py as the core framework.

## Module Organization

### Core Framework: `workflow.py`
**Purpose:** Defines all shared types, utilities, and base node implementations

**Responsibilities:**
- Data models (AOPState, ADMET_Profile, Candidate_Info, etc.)
- Helper functions (logging, JSON parsing, confidence calculations)
- Base node implementations (Initial_ADMET_node, similarity_scoring_node, critic_node, visualize)
- Graph routing logic
- Constants and configuration

**Exports:**
- TypedDict: `AOPState` - main workflow state container
- Models: `ADMET_Profile`, `MIE_Info`, `Candidate_Info`, `Candidate_List`, `Similarity_Info`, `Similarity_List`, `PathwayDecision`
- Functions: `run_agent()`, `as_dict()`, `add_provenance()`, `pathway_review()`, `calculate_confidence_metrics()`, etc.
- Node functions: `Initial_ADMET_node()`, `similarity_scoring_node()`, `critic_node()`, `visualize()`
- Constants: `MAX_ITERATIONS`, `SIMILARITY_THRESHOLD`, `MIN_PATHWAY_LENGTH`, etc.

### Specialized Modules

#### `read_across.py`
**Purpose:** Handles candidate generation and pathway expansion logic

**Dependencies:** Imports all types and utilities from `workflow.py`

**Key Functions:**
- `candidate_gen_node(state)` - Generates potential candidates (KE/AO) using aop_expert agent
- `expand_and_prune_node(state)` - Selects next pathway step and updates the pathway

**Responsibilities:**
- Chemical-specific candidate generation
- Pathway expansion with confidence scoring
- Template overlap detection and pathway uniqueness

#### `similarity_scoring.py`
**Purpose:** Scores similarity between target chemical and candidate molecules

**Dependencies:** Imports types and utilities from `workflow.py`

**Key Functions:**
- `similarity_scoring_node(state)` - Evaluates chemical similarity for candidates

**Responsibilities:**
- ADMET profile comparison
- Structural similarity assessment
- Filtering candidates by similarity threshold

#### `utils.py`
**Purpose:** Utility functions for workflow operations

**Key Components:**
- `WorkflowUtils` class with agent calling infrastructure
- Cache management for LLM responses
- Agent instruction definitions

**Responsibilities:**
- Agent runtime execution
- Response caching
- LLM interaction

### Main Orchestrator: `orchestrator.py`
**Purpose:** Ties all components together into a cohesive workflow

**Key Components:**
- `AOPOrchestrator` class - Main orchestrator
- Graph construction
- State routing logic
- Formatted output

**Workflow Sequence:**
```
START 
  ↓
Initial_ADMET (target profile + MIEs)
  ↓
candidate_gen (generate KE/AO candidates)
  ↓
Similarity_Scoring (score chemical similarity)
  ↓
expand (select best candidate, update pathway)
  ↓
critic (quality assurance checks)
  ↓
[Router Decision]
  ├→ visualize → END (if AO reached or termination condition met)
  └→ candidate_gen (if continuing)
```

## Data Flow

### AOPState Structure
The central state object that flows through all nodes:

```python
AOPState = {
    # Input
    "chemical": str,              # Target chemical name
    
    # Analysis results
    "data": {
        "target_profile": {
            "properties": {...},  # ADMET/phys-chem properties
            "liabilities": [...]  # Known adverse properties
        }
    },
    "MIEs": [...],               # Molecular Initiating Events
    
    # Pathway construction
    "AOP_pathways": [...],       # Current pathway (list of events)
    "candidates": [...],         # Generated candidate events
    "similarity_scores": [...],  # Similarity assessments
    
    # Decision making
    "confidence_score": float,   # Overall confidence (0-1)
    "confidence_breakdown": {},  # Per-component confidence scores
    "next_action": str,          # "expand" | "terminate" | "prune"
    "is_ao_reached": bool,       # Final Adverse Outcome identified?
    
    # Tracking
    "iteration_count": int,      # Current iteration number
    "provenance": [...],         # Decision audit trail
    "messages": [...]            # Agent interaction history
}
```

## Node Responsibilities

### 1. **Initial_ADMET_node** (workflow.py)
- Analyzes target chemical using admet_mie agent
- Extracts ADMET properties and liabilities
- Identifies Molecular Initiating Events (MIEs)
- Sets up target profile for downstream comparison

### 2. **candidate_gen_node** (read_across.py)
- Uses aop_expert agent to generate candidate events
- Considers current pathway depth and chemical properties
- Ranks candidates by confidence
- Handles insufficient candidate generation

### 3. **Similarity_Scoring_node** (similarity_scoring.py)
- Scores each candidate against target chemical
- Uses admet_mie agent for comparative analysis
- Filters candidates by similarity threshold
- Updates candidate list with similarity scores

### 4. **expand_and_prune_node** (read_across.py)
- Selects best candidate using aop_constructor agent
- Updates pathway with selected event
- Calculates confidence breakdown
- Detects pathway stagnation
- Decides: continue expansion or prepare termination

### 5. **critic_node** (workflow.py)
- Performs quality assurance checks
- Detects template reuse (pathway duplication)
- Identifies premature termination
- Calculates generic score for pathway specificity
- May force expansion if quality thresholds not met

### 6. **visualize** (workflow.py)
- Generates topological AOP map (PNG)
- Creates hierarchical graph: MIE → KE → AO
- Includes confidence scores and metadata
- Saves output file

## Routing Logic

### route_after_critic (orchestrator.py)
Determines next node based on termination conditions:

```
IF is_ao_reached AND pathway_depth_ok:
  → visualize (success)
ELSE IF no_progress_cycles ≥ NO_PROGRESS_LIMIT:
  → visualize (timeout)
ELSE IF next_action == "terminate":
  → visualize (normal termination)
ELSE IF no_candidate_cycles ≥ NO_CANDIDATE_LIMIT:
  → visualize (inability to continue)
ELSE IF iteration_count ≥ MAX_ITERATIONS:
  → visualize (max iterations reached)
ELSE:
  → candidate_gen (continue expansion)
```

## Configuration

### Environment Variables

```bash
# Workflow control
AOP_MAX_ITERATIONS=10                    # Maximum pathway expansion cycles
AOP_SIMILARITY_THRESHOLD=0.0             # Minimum similarity to retain candidate
AOP_MIN_PATHWAY_LENGTH=5                 # Minimum pathway events before AO
AOP_MIN_KE_STEPS=3                       # Minimum Key Events required
AOP_VERBOSE=false                        # Enable debug logging
AOP_OUTPUT_DIR=outputs                   # Output directory

# Quality thresholds
AOP_TEMPLATE_OVERLAP_THRESHOLD=0.80      # Max template reuse allowed
AOP_GENERIC_SCORE_THRESHOLD=0.70         # Max generic terminology allowed
AOP_NO_PROGRESS_LIMIT=2                  # Cycles without pathway change

# Cache and utility
ENABLE_CACHE=true                        # Cache LLM responses
CACHE_DIR=./cache                        # Cache storage location
OPENAI_MODEL=gemma-4-31b                 # LLM model to use
```

## Usage

### As a Library
```python
from orchestrator import AOPOrchestrator

orchestrator = AOPOrchestrator(verbose=True)
result = orchestrator.run("aspirin")

print(f"Pathway: {result['AOP_pathways']}")
print(f"Confidence: {result['confidence_score']:.3f}")
print(f"AO Reached: {result['is_ao_reached']}")
```

### As a Command-Line Tool
```bash
# Interactive mode
python orchestrator.py

# Direct chemical name
python orchestrator.py aspirin

# Multiple word chemical
python orchestrator.py "N-acetyl-p-aminophenol"
```

## Provenance and Audit Trail

Each decision is recorded in the `provenance` list with:
- Node identifier
- Agent responsible
- Reasoning/decision
- Timestamp
- Associated scores (confidence, similarity)
- Source hints (chemical name, file path, etc.)

This enables:
- Complete decision traceability
- Debugging pathway construction
- Identifying weak points in reasoning
- Reproducibility

## Error Handling

### Graceful Degradation
- No valid candidates → increment `no_candidate_cycles`, eventually terminate
- Weak similarity → filter candidates, may trigger termination if all fail
- Agent failures → caught and logged, state continues
- Stalled progression → force termination after `NO_PROGRESS_LIMIT` cycles

### Output Guarantee
Even if workflow terminates early or encounters errors:
- Partial pathway is retained
- Confidence scores calculated from available data
- Results saved to JSON files
- Visualization attempted on whatever pathway exists

## Extension Points

### Adding New Nodes
1. Create node function with signature: `node_func(state: AOPState) -> AOPState`
2. Register in `AOPOrchestrator._build_graph()`: `g.add_node("my_node", my_node_func)`
3. Connect with edges: `g.add_edge("predecessor", "my_node")`

### Custom Agents
Agents are defined in `workflow.py` AGENT_PROMPTS and instantiated via `run_agent()`:
- admet_mie: ADMET profile analysis and similarity
- aop_expert: Pathway event identification
- aop_constructor: Pathway decision making
- visuals_agent: Visualization rendering
- Additional agents can be added to AGENT_PATHS

### Modifying Routing
Override `_route_after_critic()` in `AOPOrchestrator` to customize decision logic.

## Testing

### Unit Tests
Each module can be tested independently:
```bash
pytest tests/test_workflow.py
pytest tests/test_read_across.py
pytest tests/test_similarity_scoring.py
```

### Integration Tests
Full workflow execution with known chemicals:
```bash
python -m pytest tests/test_orchestrator.py -v
```

### Manual Testing
```bash
python orchestrator.py "acetaminophen"
# Check outputs/
# - aop_results.json: Full results
# - *_aop_topological_map.png: Visualization
# - pathway_memory.json: Historical pathways
```

## Performance Characteristics

- **Execution Time:** 5-30 seconds per chemical (depends on pathway depth and LLM latency)
- **Memory Usage:** ~200MB for typical run
- **Cache Benefit:** ~80% faster on repeated chemicals with cache enabled
- **Scalability:** Single-threaded, can be parallelized across chemicals

## Known Limitations

1. **LLM Dependency:** Output quality depends entirely on LLM capabilities
2. **Chemical Coverage:** Limited by training data of agents and databases
3. **AOP Wiki Coverage:** Only documented pathways can be confidently identified
4. **No Branching:** Currently explores single main pathway, not multi-pathway analysis
5. **Visualization:** PNG generation depends on visuals_agent implementation

## Future Improvements

- [ ] Multi-pathway branching (DAG instead of linear)
- [ ] Parallel candidate evaluation
- [ ] Human-in-the-loop workflow (pause for expert review)
- [ ] Real-time confidence updating
- [ ] Integration with more external AOP databases
- [ ] Comparative analysis across similar chemicals
