--
title: 'pDST-Calc: A Python package for Phenotypic Drug Susceptibility Testing in Tuberculosis'
tags:
  - python
  - bioinformatics
  - tuberculosis
  - drug-resistance

authors:
  - name: "Abhinav Sharma"
    orcid: 0000-0002-6402-6993
    equal-contrib: true
    corresponding: true
    affiliation: 1

  - name: "Bea Loubser"
    orcid: 0009-0000-9837-3339
    equal-contrib: true
    affiliation: 1

  - name: 'Gian van der Spuy'
    orcid: 0000-0002-9067-5903
    email: gvds@sun.ac.za
    affiliation: 1

  - name: 'Emilyn Costa Conceição#'
    orcid: 0000-0002-7445-6620
    email: emilyncosta@gmail.com
    affiliation: 1,3


affiliations:
  - name: SAMRC Centre for Tuberculosis Research; Division of Molecular Biology and Human Genetics, Faculty of Medicine and Health Sciences, Stellenbosch University, Cape Town, South Africa.
    index: 1
  - name: FIXME for CBCB
    index: 2
  - name: Centre for Epidemic Response and Innovation, School of Data Science and Computational Thinking, Stellenbosch University, Stellenbosch, South Africa.
    index: 3

date: 08 August 2025
bibliography: paper.bib

---


# Summary

Phenotypic Drug Susceptibility Testing (pDST) in the context of Tuberculosis (TB) is a crucial laboratory practice that determines the effectiveness of antibiotic drugs against *Mycobacterium tuberculosis* growth. The pDST-Calc Calculator is a robust Python command-line tool built to automate, standardize, and mitigate errors in pDST calculations across laboratories.

# Statement of need

Laboratory preparation for pDST involves numerous manual calculations that are time-consuming, error-prone, and require specialized knowledge. Currently, lab workers rely on written or manual spreadsheet calculations that are not only impractical but also not scalable or reliable. The pDST-Calc calculator bridges this gap by providing an open-source tool that incorporates these calculations into standardized practice.

# Development

pDST-Calc is programmed in Python and provides basic pDST calculations with simple variable inputs (i.e., drug choice, custom critical concentrations, molecular weights of purchased drugs, desired stock volume, and number of MGIT tubes the user would like to prepare) and outputs stock- and working-solution dilution measurements.

pDST calculations automated by the tool include:

- ## Drug Potency Calculation:

  $f(\text{mol}{purch}, \text{mol}{org}) = \frac{\text{mol}{purch}}{\text{mol}{org}}$

  Accounts for variations in drug purity in purchased drugs compared to their original molecular weights.

- ## Estimated Drug Weight Calculation:

  $f(\text{conc}{crit}, \text{vol}{stock}, \text{potency}) = \frac{\text{conc}{crit} \times \text{vol}{stock} \times \text{potency} \times 84}{1000}$

  Determines the estimated drug weight needed for each drug to achieve the desired final concentration in the stock solution.

- ## Diluent Volume Calculation:

  $f(\text{est}{drugweight}, \text{act}{drugweight}, \text{desired}{totalvol}) = \frac{\text{est}{drugweight}}{\text{act}{drugweight}} \times \text{desired}{totalvol}$

  Determines the volume of diluent needed to achieve the desired concentration, considering the difference between estimated and actual drug weight.

- ## Stock Solution Concentration Calculation:

  $f(\text{act}{drugweight}, \text{vol}{diluent}) = \frac{\text{act}{drugweight} \times 1000}{\text{vol}{diluent}}$

  Provides the concentration of the prepared stock solution.

- ## MGIT Concentration Calculation:

  $f(\text{crit}{concentration}) = \frac{\text{crit}{concentration} \times 8.4}{0.1}$

  Determines the final MGIT concentration by applying the dilution factor.

- ## Working Solution Volume Calculation:

  $f(\text{num}{mgits}) = \text{num}{mgits} \times 0.12 + 0.36$

  Calculates the volume of working solution needed based on the number of MGIT tubes to be prepared.

- ## Stock Solution to Working Solution Volume Calculation:

  $f(\text{vol}{workingsol}, \text{conc}{mgit}, \text{conc}{stock}) = \frac{\text{vol}{workingsol} \times \text{conc}{mgit}}{\text{conc}{stock}}$

  Determines the volume of stock solution needed to prepare the working solution.

- ## Final Diluent Volume Calculation:

  $f(\text{vol}{ss\_to\_ws}, \text{vol}{workingsol}) = \text{vol}{workingsol} - \text{vol}{ss\to\_ws}$

  Calculates the volume of diluent needed to complete the working solution.

- ## Remaining Stock Solution Volume Calculation:

  $f(\text{vol}{ss\_to\_ws}, \text{vol}{diluent}) = \text{vol}{diluent} - \text{vol}{ss\to\_ws}$

  Calculates the remaining stock solution volume by subtracting the volume of stock solution used for the working solution from the total diluent volume originally prepared, ensuring proper inventory management and waste reduction.

# Usage

The CLI application collects user inputs across the drug susceptibility testing workflow while incorporating input validation, error checking, file-name cleaning, and detailed logging to ensure accuracy and reproducibility.

The workflow begins with the user providing a session name, then selecting their desired drugs by entering comma- or space-separated numbers corresponding to the available drugs in the database. The user is then given the opportunity to customise critical concentrations of the selected drugs.

Next, the user is prompted to enter the molecular weight of their purchased drug samples and the desired stock volume for preparing their stock solutions. The first output is calculated, returned, and saved to a text file, with instructions for the user to weigh out the suggested calculated values and return to the session with the actual weighed values.

After the actual drug weights are collected, the user provides the final input of the number of MGIT tubes to be prepared per drug. At this point, pDST-Calc calculates, returns, and saves to a text file the final dilution measurements to create the stock and working solutions.

# Discussion

The aim of developing the pDST-Calc tool was to design and implement a standardized open-source Python-based command-line tool that automates drug preparation calculations for TB phenotypic drug-susceptibility testing. This will help eliminate manual errors commonly associated with laboratory preparation, reduce redundancy, and significantly cut the time required for pDST procedures — all while maintaining the accuracy and reproducibility needed for clinical applications.

# Citations

# Figures

# Acknowledgements

We acknowledge contributions from ...

# References
