<<<<<<< HEAD
# AGENTS.md

## Repository Overview 
This repository provides computational chemistry workflows using RDKit and PubChem for molecular property prediction, virtual screening, ADMET analysis, molecular docking preparation, and chemical space exploration. It also includes capabilities for predicting Adverse Outcome Pathways (AOPs) for molecules using machine learning models, databases, and simulation techniques. The agents, skills, and tools in this repository are to be used to predict the potential pathways of specific molecules, including their AOPs, ADMET scores, and toxicology analysis. The goal is for this workflow to be used for underesearched or new molecules.

## Key Files
- `README.md`: Main project documentation with setup instructions and usage examples
- `.gitignore`: Excludes `/secret` directory and `*.pdf` files from version control
- `skills-lock.json`: Skill dependencies and configurations
- `examples/example_map.py`: General example script for topological map
- `LICENSE.txt`: Project license information

## Development Commands
### Installation
```bash
pip install rdkit scikit-learn tensorflow reportlab pandas matplotlib seaborn
```

### Running Examples
```bash
python examples/carcinogenesis_map.py
python examples/example_map.py
```

## Project Structure
```
cheminformatics-aop-system/
├── data/                  # Raw and processed data
│   ├── databases/          # Database exports
│   ├── features/           # Extracted features
│   ├── models/             # Trained models
│   └── analysis/           # Pre-analyzed data
├── src/                   # Source code
│   ├── cheminformatics/    # Cheminformatics modules
│   ├── aop/                # AOP prediction modules
│   │   └── aop_wiki_api/   # AOP Wiki API client
│   └── utils/              # Utility functions
├── examples/              # Example scripts
├── skills/                # Agent skills and capabilities
│   ├── aop-pathway/        # AOP pathway analysis
│   ├── find-skills/        # Skill discovery
│   └── dontuse-admet/      # ADMET analysis (deprecated)
├── tests/                 # Test cases
├── config/                # Configuration files
├── docs/                  # Documentation
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
└── README.md              # Project documentation
```

## Notes
- The repository focuses on cheminformatics and AOP prediction
- Uses RDKit for molecular property calculations and analysis
- Includes machine learning models for AOP prediction
- Provides visualization tools for chemical space exploration
- The `secret` directory is intentionally excluded from version control
- Includes an AOP Wiki API client for accessing external AOP data

## Important Notices
- When applicable, use skills to solve problems/tasks and create results
- For cheminformatics tasks, use the cheminformatics skill
- For AOP prediction, use the AOP prediction capabilities in the src/aop directory
- When calculating ADMET properties, scores, etc, use the skills/admet-scoring, along with the cheminformatics skill, but prioritize using scoring from the admet-scoring skill to use in parallel with cheminformatics
- All file operations must be confined to the current directory (`/home/avam11/lively-animatronic-llama`)
- No external directory access is permitted to save files to regardless of skill(s) used

## Usage Examples
- Use the `generate_orforglipron_aop.py` script to generate AOP predictions for specific molecules
- Run `aspirin aop/analyze_aspirin.py` for aspirin-specific AOP analysis examples
- Check `skills/aop-pathway/SKILL.md` for detailed AOP pathway analysis capabilities
=======
# Automated Screening of Adverse Outcomes

The purpose of this project is, given the name of a chemical compound, to determine any potential hazards and risks associated with that compound. Key techniques include literature review, in silico toxicology, and adverse-outcome pathways. Together, AOPs, literature review, and in silico methods form a complementary workflow: the literature provides the evidence, AOPs organize it mechanistically, and computational toxicology helps fill gaps, prioritize chemicals, and generate testable hypotheses.

## Adverse outcome pathways 
Adverse outcome pathways (AOPs) are structured frameworks that link a molecular initiating event—like a chemical binding to a receptor or enzyme—to a chain of key biological events that ultimately leads to an adverse outcome relevant to health or ecology. They’re used to organize toxicology knowledge in a way that helps explain how a chemical causes harm, not just whether it does.

## Literature review
Literature review is central to AOP development. Researchers systematically scan the published evidence to identify known key events, supporting studies, dose-response relationships, and biological plausibility. Good AOP reviews pull together data from experimental toxicology, mechanistic biology, epidemiology, and sometimes clinical or ecological studies to build and evaluate the pathway. The literature is also used to assess the weight of evidence for each connection in the pathway.

## In silico toxicology
In silico toxicology techniques support AOPs by using computational methods to predict or analyze toxic effects without new wet-lab experiments. Common tools include:
- QSAR models to predict toxicity from chemical structure
- Read-across to infer hazard from similar compounds
- Molecular docking / simulation to identify possible molecular initiating events
- Pathway and network analysis to map gene/protein interactions
- Machine learning to predict key events or adverse outcomes from large datasets

# Technical terms

Toxicology and related fields sometimes have field-specific, technical definitions for otherwise common words. Read the reference file: [Disambiguated Technical Terms](@{REF}:/glossary/disambiguated_technical_terms.md). Note that sometimes, these words really are used in their common sense. Use surrounding context to decide which definition is being used at any given time.

In addition to these, you may come across a new term that does not have a common use. In those cases, first check the other glossary files in order to see if it is defined there:

- [Domain-Specific Terms](@{REF}:/glossary/domain_specific_terms.md)
- [Tech Glossary](@{REF}:/glossary/tech_glossary.md)

# General rules

- Never call the glob tool with the exact same search pattern twice in a row.
- Use available skills proactively when the task matches them.
- Choose the most relevant skill automatically based on the request.
- Do not require the user to name a skill unless the task is ambiguous.
- For any request involving PDFs, scan the PDF content, extract relevant information, and use the PDF skill by default.
>>>>>>> brl/main
