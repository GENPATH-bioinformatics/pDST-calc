# Figures for JOSS Publication

## Figure 1: Workflow Diagrams

The pDST-Calc workflow is illustrated through two complementary diagram formats:

### ASCII Workflow Diagram (figure1.txt)

A text-based flowchart showing the complete pDST-Calc calculation pipeline from initial drug selection to final laboratory-ready output. This format ensures compatibility with all publication systems and maintains clarity in black and white printing.

### Mermaid Workflow Diagram (figure1_mermaid.mmd)

A modern, color-coded flowchart that provides the same workflow information with enhanced visual appeal. The diagram uses color coding to distinguish different phases:
- **Blue (Input Phase)**: Drug selection, critical concentrations, molecular weights
- **Pink (Calculation Phases)**: Mathematical computations and algorithms
- **Orange (Laboratory Work)**: Physical weighing and data input
- **Green (Output Phase)**: Results generation and export

## Workflow Content

Both diagrams illustrate:

**Input Phase**: 
- Drug selection from 22 WHO-standardized anti-TB drugs
- Optional critical concentration customization
- Input of purchased molecular weights and stock volumes

**Calculation Phase 1**:
- Drug potency calculation accounting for purity variations
- Estimated drug weight calculation for target concentrations
- Generation of weighing instructions for laboratory use

**Physical Laboratory Work**:
- Actual drug weighing (outside software scope)
- Input of actual weights and MGIT tube quantities

**Calculation Phase 2**:
- Diluent volume calculation considering actual weights
- Stock solution concentration determination
- Working solution preparation calculations

**Output Phase**:
- Laboratory-ready protocols with step-by-step instructions
- Detailed calculation logs for audit trails
- CSV export for laboratory information management systems

## Usage Guidelines

**For JOSS Manuscript**: Use the ASCII version (figure1.txt) for maximum compatibility with the journal's publication system.

**For Presentations/Documentation**: Use the Mermaid version (figure1_mermaid.mmd) for enhanced visual appeal in slides, documentation, or web-based materials.

**For GitHub README**: The Mermaid diagram renders automatically in GitHub and provides an attractive visual for the repository.

## Technical Notes

- Both diagrams represent the same logical workflow
- The Mermaid version can be rendered using any Mermaid-compatible tool
- Color coding in Mermaid version helps distinguish workflow phases
- ASCII version maintains full readability in any text environment
