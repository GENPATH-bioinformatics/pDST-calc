from shiny import reactive
from shiny.express import input, render, ui
import pandas as pd
from db.src.drug_database import load_drug_data

ui.page_opts(title="pDST-Calc", description="Phenotypic Drug Susceptibility Testing Calculator")

ui.tags.div(style="margin-bottom: 30px;")

# Read the first column from the CSV file
drug_options = load_drug_data()
drug_selection = drug_options.iloc[:, 0].dropna().tolist()

# Create a Markdown stream
output_stream = ui.MarkdownStream("output_stream")

ui.input_selectize(
    "drug_selection",
    "Select Drugs",
    drug_selection,
    multiple=True,
)

ui.tags.div(style="margin-bottom: 30px;")

@render.data_frame
def generate_table():
    selected = input.drug_selection()
    if not selected:
        # Show empty DataFrame or all if nothing selected
        return render.DataGrid(drug_options.iloc[0:0])
    filtered = drug_options[drug_options.iloc[:, 0].isin(selected)]
    return render.DataGrid(filtered)


