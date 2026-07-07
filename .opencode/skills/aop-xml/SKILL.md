---
name: aop-xml
description: Provides detailed instructions for analyzing XML data from the OECD AOP database. Contains technical details about XML structure and query patterns, and implementation strategies. Use this skill when answering questions that require exact data extraction from the AOP database, such as "what is", "how many", "which record", "what status", "what ID", or "find the entry" queries.
---
## XML File Location
The XML file can be found at [data/aop-knowledge-base.xml](data/aop-knowledge-base.xml)

## XML File Structure

### Main Data Collections
The data is organized into independent collections:

1. **`<aops>`**: Contains full pathways linking events together
2. **`<key-events>`**: Contains specific biological milestones (MIEs, KEs, AOs)
3. **`<key-event-relationships>`**: Contains structural edges linking one event to another
4. **`<stressors>` & `<chemicals>`**: Chemical triggers initiating pathways
5. **`<taxonomy>`, `<cell-terms>`, `<organ-terms>`**: Biological context parameters

## Key Data Elements

### Pathway Metadata
To examine a whole pathway, look inside the `<aop>` element:
- **Title and Status**: Found in `<title>`, `<oecd-status>`, and `<saaop-status>` tags
- **Chain of Events**: Listed in the `<key-events>` sub-block
- **Network Connections**: Mapped in the `<key-event-relationships>` sub-block

### Key Events (KE)
Biological endpoints are stored independently under `<key-events>`:
- **Biological Level**: Found in `<level-of-biological-organisation>` (e.g., molecular, cellular, organ)
- **Ontology Components**: Found in `<event-components>`, which contains:
  - `<biological-process>`
  - `<biological-object>`
  - `<biological-action>`

### Key Event Relationships (KER)
The logic between causing and effect events is stored under `<key-event-relationships>`:
- **Connections**: Found in `<upstream-id>` and `<downstream-id>` tags
- **Evidence Strength**: Found in `<weight-of-evidence>` and `<quantitative-understanding>` tags

## Query Patterns

### Finding Specific AOPs
```python
# Parse XML and find AOP by ID
for aop in data['aops']:
    if aop['@id'] == target_id:
        return aop
```

### Looking Up Key Events
```python
# Create lookup map for efficient access
ke_map = {ke['@id']: ke for ke in data['key-events']}

# Retrieve specific KE by ID
ke = ke_map[event_id]
```

### Tracing Pathways
```python
# Start from MIE and trace through KERs
def trace_pathway(mie_id, data):
    current_id = mie_id
    pathway = []
    
    while current_id:
        ke = ke_map[current_id]
        pathway.append(ke)
        
        # Find next KER
        next_ker = next(
            (ker for ker in data['key-event-relationships'] 
             if ker['upstream-id'] == current_id),
            None
        )
        
        if next_ker:
            current_id = next_ker['downstream-id']
        else:
            break
    
    return pathway
```

### Finding Chemicals for an AOP
```python
# Find stressors/chemicals associated with an AOP
def find_chemicals(aop_id, data):
    aop = next(aop for aop in data['aops'] if aop['@id'] == aop_id)
    mie_id = aop['key-events'][0]['@id']  # First KE is typically MIE
    
    # Find stressors linked to MIE
    stressors = [
        stressor for stressor in data['stressors']
        if stressor.get('mie-id') == mie_id
    ]
    
    return stressors
```

## Common Query Examples

### 1. Find MIE for a specific AOP
```python
# Get first KE which is typically the MIE
def get_mie(aop_id, data):
    aop = next(aop for aop in data['aops'] if aop['@id'] == aop_id)
    return aop['key-events'][0]
```

### 2. Get all biological levels in a pathway
```python
# Extract biological organization levels
def get_biological_levels(aop_id, data):
    aop = next(aop for aop in data['aops'] if aop['@id'] == aop_id)
    ke_ids = [ke['@id'] for ke in aop['key-events']]
    
    levels = set()
    for ke_id in ke_ids:
        ke = ke_map[ke_id]
        levels.add(ke['level-of-biological-organisation'])
    
    return sorted(levels)
```

### 3. Find evidence strength for KER
```python
# Get weight of evidence for specific relationship
def get_ker_evidence(upstream_id, downstream_id, data):
    ker = next(
        (ker for ker in data['key-event-relationships']
         if ker['upstream-id'] == upstream_id and 
            ker['downstream-id'] == downstream_id),
        None
    )
    
    if ker:
        return {
            'weight_of_evidence': ker.get('weight-of-evidence', 'Unknown'),
            'quantitative_understanding': ker.get('quantitative-understanding', 'Unknown')
        }
    return None
```

### 4. Find most frequent MIEs across pathways
```python
# Analyze MIEs across all AOPs
def find_frequent_miess(data):
    mie_counts = Counter()
    
    for aop in data['aops']:
        if aop['key-events']:
            mie_id = aop['key-events'][0]['@id']
            mie_counts[mie_id] += 1
    
    # Get top 10 most frequent MIEs
    return mie_counts.most_common(10)
```

## Implementation Notes

### Parsing Strategy
1. Parse the entire XML file once using a library like `xmltodict`
2. Create lookup dictionaries for efficient access:
   - `ke_map`: Key events by ID
   - `ker_map`: Key event relationships by (upstream, downstream) pair
   - `aop_map`: AOPs by ID

### Performance Considerations
- The XML file can be large, so parse it once and cache the parsed data
- Use dictionary lookups instead of linear searches
- For complex queries, consider building indexes for frequently accessed data

### Error Handling
- Handle missing elements gracefully
- Validate IDs before lookup
- Provide meaningful error messages when data is not found

## Integration with AOP Agent

When the main AOP agent needs to query XML data, it should:
1. Load this skill
2. Use the provided query patterns
3. Return structured results to the main agent
4. Handle any XML-specific errors appropriately
