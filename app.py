import dash
from dash import dcc, html, Input, Output, ctx, dash_table
import pandas as pd
import os

# Load data from CSV (updated by scraper.py)
DATA_FILE = "bills.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Chamber", "Day", "Committee Name", "Bill Number", "Bill Author", "Caption", "Stance"])

df = load_data()

app = dash.Dash(__name__)
server = app.server

# Layout
app.layout = html.Div([
    html.H1("Texas Legislature Bills Dashboard", style={'textAlign': 'center'}),

    html.Div([
        dcc.Dropdown(
            id="chamber-filter",
            options=[{"label": ch, "value": ch} for ch in df["Chamber"].unique()],
            placeholder="Select Chamber",
            multi=True,
            style={'width': '50%', 'margin': 'auto'}
        ),
        dcc.Dropdown(
            id="day-filter",
            options=[{"label": day, "value": day} for day in df["Day"].unique()],
            placeholder="Select Day",
            multi=True,
            style={'width': '50%', 'margin': 'auto', 'marginTop': '10px'}
        ),
        dcc.Dropdown(
            id="committee-filter",
            options=[{"label": com, "value": com} for com in df["Committee Name"].unique()],
            placeholder="Select Committee",
            multi=True,
            style={'width': '50%', 'margin': 'auto', 'marginTop': '10px'}
        )
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),

    # Data Table
    html.Div([
        dash_table.DataTable(
            id="bill-table",
            columns=[{"name": col, "id": col, "editable": True} for col in df.columns],
            data=df.to_dict("records"),
            style_table={'overflowX': 'auto', 'width': '95%', 'margin': 'auto'},
            editable=True,
            row_selectable="multi",
            filter_action="native",
            sort_action="native",
            page_size=20
        )
    ], style={'textAlign': 'left', 'marginLeft': '20px'}),

    html.Div([
        html.Button("Save CSV", id="save-button", n_clicks=0, style={'marginTop': 20})
    ], style={'textAlign': 'center'}),

    dcc.Download(id="download-dataframe-csv")
])

@app.callback(
    Output("bill-table", "data"),
    [Input("chamber-filter", "value"),
     Input("day-filter", "value"),
     Input("committee-filter", "value")]
)
def update_table(selected_chambers, selected_days, selected_committees):
    df = load_data()
    filtered_df = df.copy()

    if selected_chambers:
        filtered_df = filtered_df[filtered_df["Chamber"].isin(selected_chambers)]
    
    if selected_days:
        filtered_df = filtered_df[filtered_df["Day"].isin(selected_days)]

    if selected_committees:
        filtered_df = filtered_df[filtered_df["Committee Name"].isin(selected_committees)]
    
    return filtered_df.to_dict("records")

if __name__ == '__main__':
    app.run_server(debug=False, host="0.0.0.0", port=8080)
