from shiny import App, ui, render
import pandas as pd
from core.drug_database import load_drug_data

drug_df = load_drug_data()

app_ui = ui.page_fluid(
    ui.input_selectize("drugs", "Select Drugs", choices=list(drug_df["Drug"]), multiple=True),
    ui.output_table("drug_table")
)

def server(input, output, session):
    @output
    @render.table
    def drug_table():
        selected = input.drugs()
        if not selected:
            return pd.DataFrame()
        return drug_df[drug_df["Drug"].isin(selected)]

app = App(app_ui, server)