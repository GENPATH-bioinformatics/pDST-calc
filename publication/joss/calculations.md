# Formulas

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
