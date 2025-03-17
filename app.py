import dash
from dash import dcc, html, Input, Output, ctx, dash_table, no_update
import dash_auth
import pandas as pd
import plotly.express as px
import os


VALID_USERS = {
    "tythedataguy": "imprettycool"
    "taylorb": "ilovetysomuch",
    "leahc": "thisisdope",
    "arielt": "iacceptgalleons"
}

# Define CSV file path
DATA_FILE = "bills.csv"

# Function to load data safely
def load_data():
    if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
        df = pd.read_csv(DATA_FILE)
        required_columns = ["Chamber", "Day", "Committee Name", "Bill Number", "Bill Author", "Caption", "Stance"]
        
        if all(col in df.columns for col in required_columns):
            return df
        else:
            print("⚠️ Warning: CSV file is missing required columns!")
            return pd.DataFrame(columns=required_columns)
    
    else:
        print("⚠️ Warning: No CSV file found! Returning empty dataframe.")
        return pd.DataFrame(columns=["Chamber", "Day", "Committee Name", "Bill Number", "Bill Author", "Caption", "Stance"])

# Load data
df = load_data()

sunburst_fig = px.sunburst(df, path=['Chamber', 'Day', 'Committee Name'])
sunburst_fig.update_layout(
    height=800,
    margin=dict(l=50, r=50, t=50, b=50)
)

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server  # Required for Render
auth = dash_auth.BasicAuth(app, VALID_USERS)

# Layout
app.layout = html.Div([
    html.H1("Texas Legislature Bills Dashboard", style={'textAlign': 'center'}),

    dcc.Graph(
        id="sunburst-chart",
        figure=sunburst_fig,
        style={"height": "800px", "width": "100%"}
    ),


    html.Div([
        dcc.Dropdown(
            id="chamber-filter",
            options=[{"label": ch, "value": ch} for ch in df["Chamber"].unique()] if not df.empty else [],
            placeholder="Select Chamber",
            multi=True,
            style={'width': '50%', 'margin': 'auto'}
        ),
        dcc.Dropdown(
            id="day-filter",
            options=[{"label": day, "value": day} for day in df["Day"].unique()] if not df.empty else [],
            placeholder="Select Day",
            multi=True,
            style={'width': '50%', 'margin': 'auto', 'marginTop': '10px'}
        ),
        dcc.Dropdown(
            id="committee-filter",
            options=[{"label": com, "value": com} for com in df["Committee Name"].unique()] if not df.empty else [],
            placeholder="Select Committee",
            multi=True,
            style={'width': '50%', 'margin': 'auto', 'marginTop': '10px'}
        )
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),

    # Data Table (Left-Aligned, Text Wrapping for Caption)
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
            page_size=20,
            style_cell={
                'textAlign': 'left',
                'whiteSpace': 'normal',  # Enables text wrapping
                'height': 'auto',  # Adjusts row height dynamically
            },
            style_data_conditional=[
                {"if": {"column_id": "Caption"}, "whiteSpace": "normal", "textAlign": "left"},
                {"if": {"column_id": "Stance"}, "whiteSpace": "normal", "textAlign": "left"},
            ]
        )
    ], style={'textAlign': 'left', 'marginLeft': '20px'}),

    # Save Button
    html.Div([
        html.Button("Save CSV", id="save-button", n_clicks=0, style={'marginTop': 20})
    ], style={'textAlign': 'center'}),

    # Download Link
    dcc.Download(id="download-dataframe-csv"),

    "Free Demo Designed by Quantitative Edge LLC"
])

# Callbacks
@app.callback(
    Output("bill-table", "data"),
    [Input("chamber-filter", "value"),
     Input("day-filter", "value"),
     Input("committee-filter", "value")]
)
def update_table(selected_chambers, selected_days, selected_committees):
    df = load_data()
    if df.empty:
        return []

    filtered_df = df.copy()

    if selected_chambers:
        filtered_df = filtered_df[filtered_df["Chamber"].isin(selected_chambers)]
    
    if selected_days:
        filtered_df = filtered_df[filtered_df["Day"].isin(selected_days)]

    if selected_committees:
        filtered_df = filtered_df[filtered_df["Committee Name"].isin(selected_committees)]
    
    return filtered_df.to_dict("records")

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("save-button", "n_clicks"),
    Input("bill-table", "data"),
    prevent_initial_call=True
)
def save_csv(n_clicks, table_data):
    if n_clicks:
        if not table_data:
            print("⚠️ No data to save!")
            return no_update

        updated_df = pd.DataFrame(table_data)

        print(f"✅ Saving {len(updated_df)} rows to CSV.")  # Debugging line

        return dcc.send_data_frame(updated_df.to_csv, "Custom Bill List.csv", index=False)

if __name__ == '__main__':
    app.run_server(debug=False, host="0.0.0.0", port=8080)
