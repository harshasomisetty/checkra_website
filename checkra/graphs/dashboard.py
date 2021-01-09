"""Instantiate a Dash app."""
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
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
    # colors = {
    #     'background': '#111111',
    #     'text': '#7FDBFF'
    # }
    # # Load DataFrame
    # # df = create_dataframe()
    # df = pd.DataFrame({
    # "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    # "Amount": [4, 1, 2, 2, 4, 5],
    # "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
    # })

    # fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")
    # fig.update_layout(
    #     plot_bgcolor=colors['background'],
    #     paper_bgcolor=colors['background'],
    #     font_color=colors['text']
    # )
    ent_cats = ["books", 'places', 'people']
    dash_app.layout = html.Div([
        html.Label("Entity Category"),
        dcc.Dropdown(
            id = "entity_category",
            options = [
                {'label': ent, 'value': ent} for ent in ent_cats
            ],
            value = ent_cats[0]
        ),
        html.Label("Available Entities"),
        dcc.Dropdown(
            id = "available_entities"
        ),

        html.Label("Mentions by Podcasters"),
        cyto.Cytoscape(
            id='mentions',
            
            layout={'name': 'breadthfirst'},
            style={'width': '400px', 'height': '500px'},
            elements=[
                {
                    'data': {'id': 'one', 'label': 'Locked'},
                    'position': {'x': 75, 'y': 75},
                    'locked': True
                },
                {
                    'data': {'id': 'two', 'label': 'Selected'},
                    'position': {'x': 75, 'y': 200},
                    'selected': True
                },
                {
                    'data': {'id': 'three', 'label': 'Not Selectable'},
                    'position': {'x': 200, 'y': 75},
                    'selectable': False
                },
                {
                    'data': {'id': 'four', 'label': 'Not grabbable'},
                    'position': {'x': 200, 'y': 200},
                    'grabbable': False
                },
                {'data': {'source': 'one', 'target': 'two'}},
                {'data': {'source': 'two', 'target': 'three'}},
                {'data': {'source': 'three', 'target': 'four'}},
                {'data': {'source': 'two', 'target': 'four'}},
            ]
        )

    ])
    init_callbacks(dash_app)

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
 
def init_callbacks(dash_app):
    @dash_app.callback(
        Output('available_entities', 'options'),
        Input('entity_category', 'value')

    )
    def update_entities(category):
        docs = collection.find({},{"_id":0, category:1})
        filtered = list(set([ent for arr in docs for ent in arr[category]]))
        # return filtered
        # print([mini for mini in ])
        return [{'label': i, 'value': i} for i in filtered]

    @dash_app.callback(
        Output("mentions", "elements"),
        Input('available_entities', 'value')
    )
    def update_graph(value):
        elements = []
        print(list(collection.find({"books":[value]},{"_id":0,"guest":1, "books":1})))
        print(value)


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
