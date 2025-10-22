# Formulae contained within pDST-Calc Core Calculations

## General Calculations (Used in Both Pathways)

### Drug Potency Calculations

#### 1. Potency (Molecular Weight Method)
**Function:** `potency(mol_purch, mol_org)`

$$f(\text{mol}_{\text{purch}}, \text{mol}_{\text{org}}) = \frac{\text{mol}_{\text{purch}}}{\text{mol}_{\text{org}}}$$

Traditional potency calculation based on molecular weight ratio. Accounts for variations in drug molecular weights between purchased and original compounds.

#### 2. Potency (Purity Method)
**Implementation:** Custom calculation in app.py

$$f(\text{purity}_{\%}) = \frac{1.0}{\text{purity}_{\%} / 100}$$

Potency calculation based solely on drug purity percentage. Used when molecular weight variations are negligible but purity affects activity.

#### 3. Potency (Combined Method)
**Implementation:** Custom calculation in app.py

$$f(\text{mol}_{\text{purch}}, \text{mol}_{\text{org}}, \text{purity}_{\%}) = \frac{1.0}{\text{purity}_{\%} / 100} \times \frac{\text{mol}_{\text{purch}}}{\text{mol}_{\text{org}}}$$

Combined potency calculation accounting for both molecular weight differences and purity variations.

### Core Working Solution Calculations

#### Estimated Drug Weight Calculation
**Function:** `est_drugweight(conc_crit, vol_stock, potency)`

$$f(\text{conc}_{\text{crit}}, \text{vol}_{\text{stock}}, \text{potency}) = \frac{\text{conc}_{\text{crit}} \times \text{vol}_{\text{stock}} \times \text{potency} \times 84}{1000}$$

Determines the estimated drug weight needed for each drug to achieve the desired final concentration in the stock solution. The factor 84 accounts for the MGIT dilution protocol.

#### Working Solution Volume Calculation
**Function:** `vol_workingsol(num_mgits)`

$$f(\text{num}_{\text{mgits}}) = (\text{num}_{\text{mgits}} \times 0.1) + 0.2$$

Calculates the volume of working solution needed based on the number of MGIT tubes to be prepared. Includes extra volume for pipetting accuracy.

#### Working Solution Concentration Calculation
**Function:** `conc_ws(crit_concentration)`

$$f(\text{crit}_{\text{concentration}}) = \frac{\text{crit}_{\text{concentration}} \times 8.4}{0.1}$$

Determines the final MGIT working solution concentration by applying the dilution factor used in MGIT testing.

## Pathway 1: With Stock Solution (make_stock=True)

### Adjusted Volume Calculation
**Function:** `calc_adjusted_volume(actual_weight, est_weight, base_volume)`

$$f(\text{actual\_weight}, \text{est\_weight}, \text{base\_volume}) = \frac{\text{actual\_weight}}{\text{est\_weight}} \times \text{base\_volume}$$

Adjusts working solution volume based on the ratio of actual to estimated drug weight.

### Stock Solution Factor Calculation
**Function:** `calc_stock_factor(actual_weight, total_stock_vol, ws_conc_ugml, potency)`

$$f(\text{actual\_weight}, \text{total\_stock\_vol}, \text{ws\_conc}, \text{potency}) = \frac{\text{actual\_weight} \times 1000}{\text{total\_stock\_vol} \times \text{ws\_conc} \times \text{potency}}$$

Calculates the concentration multiplier for stock solutions based on actual drug weight and target concentrations.

### Stock to Working Solution Volume
**Function:** `calc_volume_divided_by_factor(volume, factor)`

$$f(\text{total\_volWS}, \text{stock\_factor}) = \frac{\text{total\_volWS}}{\text{stock\_factor}}$$

Determines the volume of stock solution needed to prepare the working solution.

### Final Stock Concentration
**Function:** `calc_concentration_times_factor(concentration, factor)`

$$f(\text{ws\_conc}, \text{stock\_factor}) = \text{ws\_conc} \times \text{stock\_factor}$$

Calculates the final concentration of the prepared stock solution.

#### Intermediate Solution Volume
**Function:** `calc_intermediate_volume(stock_to_inter, final_stock_conc, inter_factor, ws_conc_ugml)`

$$f(\text{stock\_to\_inter}, \text{final\_stock\_conc}, \text{inter\_factor}, \text{ws\_conc}) = \frac{\text{stock\_to\_inter} \times \text{final\_stock\_conc}}{\text{inter\_factor} \times \text{ws\_conc}}$$

Calculates the total volume of intermediate dilution needed when direct dilution is impractical.

## Pathway 2: Without Stock Solution (make_stock=False)

### Direct Diluent Volume Calculation
**Function:** `calc_adjusted_volume(actual_weight, est_weight, ws_vol_ml)` (repurposed)

$$f(\text{actual\_weight}, \text{est\_weight}, \text{ws\_vol\_ml}) = \frac{\text{actual\_weight}}{\text{est\_weight}} \times \text{ws\_vol\_ml}$$

Calculates the final diluent volume needed for direct preparation of working solution without intermediate stock solutions.

### Stock Solution Concentration (Legacy)
**Function:** `conc_stock(act_drugweight, vol_diluent)`

$$f(\text{act\_drugweight}, \text{vol\_diluent}) = \frac{\text{act\_drugweight} \times 1000}{\text{vol\_diluent}}$$

Provides the concentration of the prepared solution in μg/mL (used for reference calculations).

### Volume Adjustment Calculation
**Function:** `vol_diluent(est_drugweight, act_drugweight, desired_totalvol)`

$$f(\text{est\_drugweight}, \text{act\_drugweight}, \text{desired\_totalvol}) = \frac{\text{act\_drugweight}}{\text{est\_drugweight}} \times \text{desired\_totalvol}$$

Traditional diluent volume calculation considering the difference between estimated and actual drug weight.

## Supporting Calculations

### Stock Solution to Working Solution Volume
**Function:** `vol_ss_to_ws(vol_workingsol, conc_ws, conc_stock)`

$$f(\text{vol\_workingsol}, \text{conc\_ws}, \text{conc\_stock}) = \frac{\text{vol\_workingsol} \times \text{conc\_ws}}{\text{conc\_stock}}$$

General formula for determining volume of stock solution needed to prepare working solution (used in various contexts).

### Intermediate Solution Volume Calculation
**Function:** `calc_intermediate_volume(stock_to_inter, final_stock_conc, inter_factor, ws_conc_ugml)`

$$f(\text{stock\_to\_inter}, \text{final\_stock\_conc}, \text{inter\_factor}, \text{ws\_conc}) = \frac{\text{stock\_to\_inter} \times \text{final\_stock\_conc}}{\text{inter\_factor} \times \text{ws\_conc}}$$

Calculates the total volume of intermediate dilution needed.

## Utility Calculations

### Volume Difference Calculation
**Function:** `calc_volume_difference(total_volume, volume_to_subtract)`

$$f(\text{total\_volume}, \text{volume\_to\_subtract}) = \text{total\_volume} - \text{volume\_to\_subtract}$$

General function for calculating diluent volumes or remaining volumes.

### Final Diluent Volume Calculation

$$f(\text{vol\_workingsol}, \text{vol\_stock→ws}) = \text{vol\_workingsol} - \text{vol\_stock→ws}$$

Calculates the volume of diluent needed to complete the working solution.

### Remaining Stock Solution Volume Calculation

$$f(\text{vol\_diluent}, \text{vol\_stock→ws}) = \text{vol\_diluent} - \text{vol\_stock→ws}$$

Calculates the remaining stock solution volume for inventory management and waste reduction.

---

## Units and Conventions

- **Concentrations:** μg/mL for critical concentrations and working solutions
- **Volumes:** mL for all volume measurements
- **Weights:** mg for drug weights
- **Molecular Weights:** g/mol

All calculations maintain unit consistency and include appropriate conversion factors (e.g., ×1000 for mg to μg conversions).
