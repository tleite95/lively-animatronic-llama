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

- Use available skills proactively when the task matches them.
- Choose the most relevant skill automatically based on the request.
- Do not require the user to name a skill unless the task is ambiguous.
- For any request involving PDFs, scan the PDF content, extract relevant information, and use the PDF skill by default.
