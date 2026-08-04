# Glossary of Tools for Computational Toxicology

## Bioactivity, Hazard, and Exposure Data Access

### CTX APIs / Computational Toxicology and Exposure APIs
Documentation: https://comptox.epa.gov/ctx-api/docs/  
EPA CTX APIs provide programmatic access to chemical, hazard, bioactivity, and exposure data used in computational toxicology workflows, including data connected to the CompTox Chemicals Dashboard . They are useful for automated retrieval of chemical identifiers, assay results, toxicity data, and exposure information for modeling pipelines .

### ctx-python
Documentation: https://www.epa.gov/comptox-tools/computational-toxicology-and-exposure-apis-clients  
`ctx-python` is a Python client package for accessing EPA CTX APIs without manually constructing HTTP requests . It is useful for scripting chemical lookup, hazard-data retrieval, bioactivity queries, and exposure-data integration in Python-based workflows .

### ctxR
Documentation: https://www.epa.gov/comptox-tools/computational-toxicology-and-exposure-apis-clients  
`ctxR` is an R client package for accessing EPA CTX APIs, with CRAN-hosted vignettes and examples for reproducible use . It is useful for retrieving CompTox-linked chemical, exposure, bioactivity, and hazard data directly into R analysis pipelines .

### PubChem PUG-REST
Documentation: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest  
PubChem PUG-REST is a public REST API for retrieving chemical structures, identifiers, properties, bioassay records, and compound annotations. It is widely used to normalize chemical identifiers, enrich compound tables, and link toxicology datasets to public chemical records.

### PubChemPy
Documentation: https://pubchempy.readthedocs.io/  
PubChemPy is a Python wrapper for PubChem PUG-REST that enables scripted retrieval of compound, substance, assay, and identifier data. It is useful for chemical-name resolution, CID lookup, SMILES/InChI retrieval, and batch chemical annotation.


## Cheminformatics and Molecular Representation

### Chemistry Development Kit (CDK)
Documentation: https://cdk.github.io/  
CDK is a Java cheminformatics library for molecular representation, descriptor calculation, substructure searching, fingerprinting, and chemical file parsing. OPERA documents CDK as one of the descriptor engines used in its QSAR models, supporting its relevance to computational toxicology workflows .

### Mordred
Documentation: https://mordred-descriptor.github.io/documentation/master/  
Mordred is a Python molecular-descriptor calculator that computes a large set of 2D and 3D descriptors from chemical structures. It is commonly used to generate QSAR-ready feature matrices from SMILES, SDF, or RDKit molecule objects.

### MolVS
Documentation: https://molvs.readthedocs.io/  
MolVS is a Python library for molecule validation and standardization built on RDKit. It is useful for salt stripping, charge normalization, tautomer handling, fragment selection, and preparing consistent QSAR-ready structures.

### Open Babel
Documentation: https://open-babel.readthedocs.io/  
Open Babel is a command-line and library toolkit for converting, filtering, searching, and manipulating chemical file formats. It is useful for high-throughput conversion among SMILES, SDF, MOL2, PDB, InChI, and related formats in automated toxicology workflows.

### PaDEL-Descriptor
Documentation: http://www.yapcwsoft.com/dd/padeldescriptor/  
PaDEL-Descriptor is a Java-based descriptor and fingerprint calculator that can be run from the command line for batch molecular feature generation. OPERA documents PaDEL as one of the descriptor engines used in its QSAR models, supporting its role in computational toxicology pipelines .

### RDKit
Documentation: https://www.rdkit.org/docs/  
RDKit is a cheminformatics toolkit for molecular parsing, standardization, fingerprinting, substructure searching, descriptor calculation, and structure-based machine learning. It is often used as the core chemical-processing layer for QSAR, read-across, clustering, and data-curation workflows.


## QSAR, Read-Across, and Predictive Toxicology

### DeepChem
Documentation: https://deepchem.readthedocs.io/  
DeepChem is a Python framework for machine learning on molecular, biological, and materials data, including graph neural networks, molecular featurizers, and model-training utilities. It is useful for building toxicity-prediction models from molecular structures, assay matrices, and multitask bioactivity datasets.

### lazar
Documentation: https://github.com/opentox/lazar  
`lazar` is an open-source read-across and QSAR system for predicting chemical properties and toxicological endpoints from structurally similar compounds. It is useful for interpretable local modeling, similarity-based endpoint estimation, and reproducible toxicological prediction workflows.

### OPERA
Documentation: https://github.com/kmansouri/OPERA  
OPERA is a free and open-source/open-data suite of QSAR models for physicochemical properties, environmental fate, and toxicity endpoints, with command-line availability for Windows and Linux . Its documented models include Caco-2 permeability, human plasma fraction unbound, hepatic intrinsic clearance, pKa, LogD, estrogen-receptor activity, androgen-receptor activity, CATMoS acute-toxicity outputs, bioconcentration factor, biodegradation half-life, vapor pressure, water solubility, and related endpoints .

### Toxtree
Documentation: https://toxtree.sourceforge.net/  
Toxtree is an open-source application for applying structural alerts, decision trees, and rule-based toxicological classification schemes. It is useful for automated screening of chemical structures against expert-rule systems such as Cramer classes and structural-alert workflows.


## High-Throughput Screening and Assay Analysis

### invitroTKstats
Documentation: https://cran.r-project.org/package=invitroTKstats  
`invitroTKstats` is an R package for statistical analysis of in vitro toxicokinetic data. It is useful for estimating parameters such as fraction unbound, intrinsic clearance, and other quantities needed for in vitro–to–in vivo extrapolation workflows.

### tcpl / ToxCast Pipeline
Documentation: https://cran.r-project.org/package=tcpl  
`tcpl` is an R package for processing and modeling high-throughput screening concentration-response data from ToxCast-style assays. EPA notes that the ToxCast Pipeline R package can use CTX Bioactivity APIs as a connection option for data retrieval and plotting .

### ToxPi
Documentation: https://github.com/ToxPi/ToxPi-GUI  
ToxPi is an open-source framework for integrating multiple evidence streams into Toxicological Priority Index profiles. It is useful for ranking chemicals, visualizing multidimensional toxicological evidence, and combining assay, exposure, and hazard indicators.

### toxEval
Documentation: https://code.usgs.gov/water/toxEval  
`toxEval` is an R package for evaluating chemical-mixture toxicity using concentration data and benchmark values. It is useful for screening environmental monitoring datasets for chemicals and mixtures that may exceed toxicological concern thresholds.


## Toxicokinetics, PBPK, and Pharmacometric Simulation

### GNU MCSim
Documentation: https://www.gnu.org/software/mcsim/  
GNU MCSim is an open-source simulation and statistical inference package for dynamic models, including pharmacokinetic and physiologically based toxicokinetic models. It is useful for Monte Carlo simulation, Bayesian calibration, sensitivity analysis, and population variability modeling.

### httk
Documentation: https://cran.r-project.org/package=httk  
`httk` is an R package for high-throughput toxicokinetics and in vitro–to–in vivo extrapolation. It is useful for estimating steady-state concentrations, reverse dosimetry, toxicokinetic parameters, and chemical-specific exposure equivalents.

### mrgsolve
Documentation: https://mrgsolve.org/  
`mrgsolve` is an R package for simulation from ODE-based pharmacokinetic, pharmacodynamic, and systems models. It is useful for scripted toxicokinetic and PBPK-style simulation, virtual-population analysis, and dose-scenario exploration.

### ospsuite-R
Documentation: https://www.open-systems-pharmacology.org/  
`ospsuite-R` provides an R interface to Open Systems Pharmacology models, enabling scripted simulation, parameter changes, and model analysis without relying on the graphical interface. Open Systems Pharmacology describes PK-Sim and MoBi as modeling and simulation tools for PBPK, PBPK/PD, and quantitative systems pharmacology, with extensive documentation and community use .

### ospsuite-python
Documentation: https://www.open-systems-pharmacology.org/  
`ospsuite-python` provides Python access to Open Systems Pharmacology models for headless simulation and workflow integration. It is useful for automated PBPK model execution, scenario testing, parameter manipulation, and downstream analysis in Python-based computational toxicology workflows .

### PK-Sim CLI
Documentation: https://docs.open-systems-pharmacology.org/working-with-pk-sim/pk-sim-documentation/pk-sim-command-line-interface  
PK-Sim is a whole-body physiologically based pharmacokinetic modeling tool with an integrated database of anatomical and physiological parameters for humans and common laboratory animals . Its documentation includes a command-line interface, making it usable in scripted PBPK simulation and batch-processing workflows .


## Molecular Interaction, Docking, and Mechanistic Modeling

### AutoDock Vina
Documentation: https://autodock-vina.readthedocs.io/  
AutoDock Vina is an open-source command-line molecular docking tool for predicting ligand binding poses and approximate binding affinities. It is useful for screening chemical interactions with receptors, enzymes, transporters, and other molecular targets relevant to toxicological mechanisms.

### COPASI
Documentation: https://copasi.org/Support/User_Manual/  
COPASI is an open-source biochemical network simulation tool with command-line support for deterministic, stochastic, steady-state, parameter-estimation, and sensitivity analyses. It is useful for modeling toxicodynamic pathways, signaling networks, enzymatic systems, and mechanistic adverse outcome components.

### OpenMM
Documentation: https://docs.openmm.org/  
OpenMM is an open-source molecular simulation toolkit for molecular dynamics and custom force-field workflows. It is useful for mechanistic studies of ligand–protein interactions, membrane partitioning, conformational behavior, and molecular-level determinants of toxicity.


## Environmental Fate, Mixtures, and Life-Cycle Toxicity

### USEtox
Documentation: https://usetox.org/  
USEtox is a consensus model for characterizing human toxicity and ecotoxicity impacts of chemical emissions in life-cycle assessment. It is useful for estimating characterization factors and comparing toxicological impacts across chemicals, compartments, and emission scenarios.

### enviPath
Documentation: https://envipath.org/  
enviPath is an open science platform and API-oriented resource for environmental contaminant biotransformation pathways and prediction. It is useful for identifying known and predicted transformation products, biodegradation pathways, and microbial transformation rules.

### patRoon
Documentation: https://rickhelmus.github.io/patRoon/  
`patRoon` is an R-based workflow system for non-target and suspect screening of environmental chemical data. It is useful for automated processing of high-resolution mass spectrometry data, annotation of unknowns, and integration with cheminformatics resources.


## Workflow and Reproducible Modeling Support

### KNIME Batch Executor
Documentation: https://docs.knime.com/  
KNIME workflows can be executed headlessly using batch execution, enabling GUI-designed workflows to be run in automated pipelines. It is useful when computational toxicology teams need reproducible cheminformatics, QSAR, data-cleaning, or reporting workflows without interactive execution.

### Nextflow
Documentation: https://www.nextflow.io/docs/latest/  
Nextflow is an open-source workflow language and execution engine for reproducible computational pipelines. It is useful for orchestrating multi-step toxicology workflows involving chemical standardization, descriptor generation, model prediction, assay processing, and report generation.

### Snakemake
Documentation: https://snakemake.readthedocs.io/  
Snakemake is an open-source workflow management system for reproducible and scalable data analysis. It is useful for building transparent computational toxicology pipelines that combine command-line tools, R scripts, Python scripts, databases, and model outputs.