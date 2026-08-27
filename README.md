# Adverse Outcome Pathway (AOP) Prediction System

## Overview
This project provides computational chemistry workflows using RDKit for molecular property prediction, virtual screening, ADMET analysis, molecular docking preparation, and chemical space exploration. It also includes capabilities for predicting Adverse Outcome Pathways (AOPs) for molecules using machine learning models, databases, and simulation techniques.

## Project Goals
- Calculate molecular properties and descriptors using RDKit
- Screen compound libraries for drug-likeness
- Predict ADMET properties for compounds
- Perform molecular similarity searches
- Prepare structures for molecular docking
- Visualize chemical space and structure-activity relationships
- Predict AOPs for new molecules using known data and machine learning
- Provide known AOPs for reference molecules
- Generate comprehensive reports in PDF format
- Build a scalable system for cheminformatics and AOP analysis

## Technology Stack
- **Primary Language**: Python
- **Key Libraries**: 
  - RDKit for chemical informatics and molecular property calculations
  - scikit-learn for machine learning
  - TensorFlow/PyTorch for deep learning
  - ReportLab for PDF generation
  - Requests for API interactions
  - Pandas for data manipulation
  - Matplotlib/Seaborn for visualization

## Data Sources
- **Public Databases**:
  - AOP-Wiki
  - ChEMBL
  - PubChem
  - CTDbase
  - Other toxicology and chemical databases

## System Architecture

### Core Components
1. **Molecular Property Calculation**: Calculate descriptors, drug-likeness, and ADMET properties
2. **Virtual Screening**: Filter compounds based on Lipinski's Rule of Five and other criteria
3. **Molecular Similarity Search**: Find similar compounds using fingerprint-based methods
4. **ADMET Analysis**: Predict absorption, distribution, metabolism, excretion, and toxicity properties
5. **AOP Prediction**: Predict adverse outcome pathways using machine learning models
6. **Report Generation**: Create comprehensive PDF and markdown reports with predictions
7. **Visualization**: Generate chemical space visualizations and structure-activity relationship plots

### Workflow
1. **Input**: Molecule structure (SMILES, InChI, or SDF), all known relevant information
2. **Molecular Property Calculation**: Calculate molecular descriptors and properties
3. **Drug-likeness Filtering**: Apply Lipinski's Rule of Five and other filters
4. **ADMET Prediction**: Predict ADMET properties
5. **Database Search**: Check for known AOPs in reference databases
6. **AOP Prediction**: Run ML models for AOP prediction
7. **Similarity Search**: Find similar compounds in chemical libraries
8. **Report Generation**: Create PDF report with all findings and visualizations

## Setup Instructions

### Prerequisites
- Python 3.8+
- RDKit
- scikit-learn
- TensorFlow/PyTorch
- ReportLab
- Pandas
- Matplotlib/Seaborn

### Installation
```bash
pip install rdkit scikit-learn tensorflow reportlab pandas matplotlib seaborn
```

### Configuration
Edit configuration files to specify database connections, model parameters, and other settings.


## Usage

### Calculating Molecular Properties
```python
from rdkit import Chem
from rdkit.Chem import Descriptors

mol = Chem.MolFromSmiles('CCO')
molecular_weight = Descriptors.MolWt(mol)
logp = Descriptors.MolLogP(mol)
```

### Predicting ADMET Properties
```python
from cheminformatics import admet_flags

props = {
    "logp": 3.5,
    "tpsa": 120,
    "mw": 300
}
admet_warnings = admet_flags(props)
```

### Performing Similarity Search
```python
from cheminformatics import similarity_search

query_smiles = "CCO"
library = ["CCO", "CCN", "O=Cc1ccccc1"]
results = similarity_search(query_smiles, library, threshold=0.7)
```

### Predicting AOPs
```python
from aop_prediction import predict_aop

smiles = "CCO"
prediction = predict_aop(smiles)
```

## Project Structure
```
cheminformatics-aop-system/
├── data/                  # Raw and processed data
│   ├── databases/          # Database exports
│   ├── features/           # Extracted features
│   ├── models/             # Trained models
│   └── analysis/           # Pre-analyzed data (e.g., carcinogenesis_analysis.json)
├── src/                   # Source code
│   ├── cheminformatics/    # Cheminformatics modules
│   │   ├── properties.py   # Molecular property calculations
│   │   ├── admet.py        # ADMET analysis
│   │   ├── similarity.py   # Similarity search
│   │   └── visualization.py # Visualization tools
│   ├── aop/                # AOP prediction modules
│   │   ├── prediction.py   # AOP prediction models
│   │   ├── database.py     # Database integration
│   │   └── reporting.py    # Report generation
│   └── utils/              # Utility functions
├── examples/              # Example scripts
│   ├── carcinogenesis_map.py # Carcinogenesis analysis example
│   └── example_map.py     # General example
├── topological_mapping/   # Topological mapping tools
│   ├── README.md          # Topological mapping documentation
│   └── topological_mapping_index.md # Index
├── tests/                 # Test cases
├── config/                # Configuration files
├── docs/                  # Documentation
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
└── README.md              # Project documentation
```

## Database Integration

### Supported Databases
- **AOP-Wiki**: Comprehensive AOP knowledge base
- **ChEMBL**: Bioactive compound database
- **PubChem**: Chemical substance database
- **CTDbase**: Comparative Toxicogenomics Database

### Database Connection
Configure database connections in the config directory. Example configuration for database access:

```python
# config/database_config.py
AOP_WIKI_URL = "https://aopwiki.org"
CHEMBL_API_KEY = "your_api_key_here"
```

## Analysis Examples

### Carcinogenesis Analysis
The `examples/carcinogenesis_map.py` script demonstrates how to analyze molecules for potential carcinogenic effects using the system's capabilities.

### Liver Toxicity Analysis
The `data/analysis/liver_toxicity_analysis.json` file contains pre-analyzed data on liver toxicity profiles for various compounds.

## Topological Mapping

The `topological_mapping` directory contains tools for visualizing and analyzing topological relationships between molecules and their properties. See `topological_mapping/README.md` for more details.

## Contributing
Contributions are welcome! Please follow standard practices for contributing to open source projects.

## License
See LICENSE.txt for license information.
The system uses REST APIs and direct database connections where available. API keys should be stored in the `.env` file.

## Model Training

### Training Data
- Molecular structures with known AOPs
- Biological pathway data
- Environments data
- Toxicological endpoints

### Model Types
1. **Random Forest Classifier**: For AOP classification
2. **Neural Networks**: For complex pattern recognition
3. **Similarity Models**: For known molecule matching

### Training Process
```bash
python
```

## Evaluation Metrics


## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License
This project is licensed under the BST License - see the LICENSE file for details.

## Contact
For questions or issues, please contact:

## Future Enhancements
- Integration with more databases
- Advanced simulation capabilities
- Web interface for easier access
- Batch processing for multiple molecules
- API endpoints for programmatic access
- Confirming results and integrating approved data

