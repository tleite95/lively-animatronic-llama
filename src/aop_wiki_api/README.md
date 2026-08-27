# AOP Wiki API Module

This module provides a Python client for interacting with the AOP Wiki API to retrieve Adverse Outcome Pathway (AOP) data, including Molecular Initiating Events (MIEs) and associated chemical information.

## Features

- Retrieve all Adverse Outcome Pathways (AOPs) from the AOP Wiki
- Get specific AOPs by ID
- Search for Molecular Initiating Events (MIEs)
- Find MIEs associated with specific chemicals
- Parse and model AOP data using Python dataclasses

## Installation

```bash
pip install requests
```

## Usage

### Basic Usage

```python
from aop_wiki_api import AOPWikiClient

# Create a client instance
client = AOPWikiClient()

# Get all AOPs
all_aops = client.get_all_aops()
print(f"Found {len(all_aops)} AOPs")

# Get a specific AOP by ID
aop = client.get_aop_by_id(1)
if aop:
    print(f"AOP {aop.id}: {aop.title}")
```

### Searching for Molecular Initiating Events

```python
# Search for MIEs by query
miess = client.search_miess(query="benzene")
for mie in miess:
    print(f"MIE: {mie.name}")
    if mie.chemical_name:
        print(f"  Chemical: {mie.chemical_name}")
    if mie.cas_rn:
        print(f"  CAS RN: {mie.cas_rn}")
```

### Finding MIEs for Specific Chemicals

```python
# Find MIEs for a specific chemical
miess = client.get_miess_for_chemical(chemical_name="benzene")
for mie in miess:
    print(f"MIE: {mie.name}")
    if mie.smiles:
        print(f"  SMILES: {mie.smiles}")
```

### Using Context Manager

```python
with AOPWikiClient() as client:
    aop = client.get_aop_by_id(1)
    if aop:
        print(f"AOP: {aop.title}")
        print(f"MIEs: {len(aop.molecular_initiating_events)}")
```

## Data Models

### AOP
Represents an Adverse Outcome Pathway with:
- `id`: Unique identifier
- `title`: Title of the AOP
- `description`: Description
- `key_events`: List of all key events
- `molecular_initiating_events`: Property returning only MIEs

### KeyEvent
Base class for key events with:
- `id`: Unique identifier
- `name`: Event name
- `description`: Event description
- `event_type`: Type of event
- `evidence`: Supporting evidence
- `references`: List of references

### MolecularInitiatingEvent
Extends KeyEvent with chemical-specific information:
- `chemical_name`: Name of the chemical
- `cas_rn`: CAS registry number
- `smiles`: SMILES representation
- `inchi`: InChI representation
- `inchi_key`: InChI key
- `target`: Molecular target

## Error Handling

The client raises custom exceptions for different error conditions:

- `AOPWikiError`: Base exception class
- `AOPNotFoundError`: When an AOP is not found
- `APIConnectionError`: Connection issues
- `APITimeoutError`: Request timeout
- `InvalidAPIResponseError`: Malformed responses

```python
from aop_wiki_api import AOPWikiClient, AOPNotFoundError

try:
    aop = client.get_aop_by_id(999999)  # Non-existent ID
    print(aop)
except AOPNotFoundError:
    print("AOP not found")
except Exception as e:
    print(f"Error: {e}")
```

## Development

### Testing

To test the client, you can use the provided test scripts or create your own:

```bash
python -c "
from aop_wiki_api import AOPWikiClient

client = AOPWikiClient()
print('Testing connection...')
try:
    aops = client.get_all_aops()
    print(f'Success! Found {len(aops)} AOPs')
except Exception as e:
    print(f'Error: {e}')
"
```

### Contributing

Contributions are welcome! Please follow standard Python development practices:

1. Add tests for new functionality
2. Update documentation
3. Follow PEP 8 style guidelines
4. Include type hints for new functions

## License

This module is part of the cheminformatics-aop-system project and is licensed under the same terms as the main project.

## References

- AOP Wiki: https://aopwiki.org/
- Adverse Outcome Pathways: https://aopwiki.org/about/aops
- Molecular Initiating Events: https://aopwiki.org/about/key-events/molecular-initiating-events