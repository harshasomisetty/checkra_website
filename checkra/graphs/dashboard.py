"""Instantiate a Dash app."""
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import numpy as np
import pandas as pd

from ..extensions import mongo
import plotly.express as px
import os

collection = mongo.db.lex

def init_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = dash.Dash(
        server=server,
        routes_pathname_prefix="/dummy/",
        external_stylesheets=[
            'https://codepen.io/chriddyp/pen/bWLwgP.css'
        ],
    )

    # Load DataFrame
    # df = create_dataframe()
    df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
    })

    fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

    dash_app.layout = html.Div(children=[
        dcc.Graph(
            id='example-graph',
            figure=fig
        )
    ])

    return dash_app.server, dash_app

# def create_dataframe(): #method to convert a csv to dataframe
#     """Create Pandas DataFrame from local CSV."""
#     df = pd.read_csv("checkra/data/311-calls.csv", parse_dates=["created"])
#     df["created"] = df["created"].dt.date
#     df.drop(columns=["incident_zip"], inplace=True)
#     num_complaints = df["complaint_type"].value_counts()
#     to_remove = num_complaints[num_complaints <= 30].index
#     df.replace(to_remove, np.nan, inplace=True)
#     return df
 

def create_data_table(df):
    """Create Dash datatable from Pandas DataFrame."""
    table = dash_table.DataTable(
        id="database-table",
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict("records"),
        sort_action="native",
        sort_mode="native",
        page_size=300,
    )
    return table
