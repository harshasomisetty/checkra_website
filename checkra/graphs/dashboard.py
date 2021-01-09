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

    #TODO make graph nodes smaller, make edges further away
    #TODO fix database stuff
    #TODO add links from single podcasts to entity graphs
    #TODO add links from each node in entity graph to podcast detail

    ent_cats = ['books', 'keywords','places', 'people']
    dash_app.layout = html.Div([
        html.H5(children=
            "Choose an Entity Category and a Entity to Visualize its Relations",
            style={'text-align':'center', 'padding-bottom':'10px'}
        ),
        html.Div(children=[ #options
            html.Div(children=[
                html.Small(children = "Entity Category", style = {'text-align':'center', 'padding-bottom':'10px'}),
                dcc.Dropdown(
                    id = "entity_category",
                    options = [
                        {'label': ent, 'value': ent} for ent in ent_cats
                    ],
                    value = ent_cats[0]
                )
            ], style={'display': 'inline-block','width':'200px'}),
            html.Div(children=[
                html.Small(children = "Available Entities", style = {'text-align':'center', 'padding-bottom':'10px'}),
                dcc.Dropdown(
                    id = "available_entities"
                )
            ], style={'display': 'inline-block','width':'400px', 'padding-left':'30px'}),
        ], style={'margin':'auto', 'width':'600px', 'padding-bottom':'20px'}),
        
        html.Div(children=[ #graph display
            html.Label("Mentions by Podcasters"),
            cyto.Cytoscape(
                id='mentions',
                
                layout={'name': 'concentric'},
                style={'width': '100%', 'height': '700px'},
                stylesheet=[
                    {
                        'selector': 'node',
                        'style': {
                            'content': 'data(label)'
                        }
                    },
                    {
                        'selector':'.search',
                        'style': {
                            'background-color':'red'
                        }
                    },
                    {
                        'selector':'.result',
                        'style': {
                            'background-color':'blue'
                        }
                    }
                ]
            )
        ])
        

    ]
)
    init_callbacks(dash_app)

    return dash_app.server, dash_app

 
def init_callbacks(dash_app):
    @dash_app.callback(
        Output('available_entities', 'options'),
        Output('available_entities', 'value'),
        Input('entity_category', 'value')

    )
    def update_entities(category):
        docs = collection.find({},{"_id":0, category:1})
        filtered = list(set([ent for arr in docs for ent in arr[category]]))
        all_options = [{'label': i, 'value': i} for i in filtered] #format options for dropdown
        return all_options, all_options[0]['value']

    @dash_app.callback(
        Output("mentions", "elements"),
        Input('available_entities', 'value'),
        Input('entity_category', 'value')
    )
    def update_graph(value, category):

        elements = [{'data':{"id":value, 'label':value}, 'classes':'search'}]
        for doc in collection.find({category:value},{"_id":0,"guest":1, "books":1}):
            # print(doc, "\n")
            elements.append({'data':{"id":doc["guest"], 'label':doc["guest"]}, 'classes':'result'})
            elements.append({'data':{"source":value, 'target':doc["guest"]}, 'classes':'result'})
        return elements



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
