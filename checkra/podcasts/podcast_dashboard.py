import json
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
import dash_table
import numpy as np
import pandas as pd
from flask import redirect, url_for, render_template, request, Markup, Blueprint
from ..extensions import mongo
import plotly.express as px
import os
from ..podcasts import podcasts

collection = mongo.db.lex

def init_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = dash.Dash(
        server=server,
        routes_pathname_prefix="/podcasts2dash/",
        external_stylesheets=[
            'https://codepen.io/chriddyp/pen/bWLwgP.css'
        ],
    )

    speakers = sorted([pod["guest"] for pod in list(collection.find({},{"_id":0,"guest":1}))])
    print(speakers)
    dash_app.layout = html.Div([
        html.H5(children=
            "Choose a name to explore the person's podcast",
            style={'text-align':'center', 'padding-bottom':'10px'}
        ),
        html.P(children=
            "Currently supporting podcasts by Lex Fridman",
            style={'text-align':'center', 'padding-bottom':'10px'}
        ),
        html.Div([
            dcc.Dropdown(
                id = "speakers",
                options = [
                    {'label': ent, 'value': ent} for ent in speakers
                ],
                value=speakers[0]
            )
        ], style={'width':'300px', 'margin':'auto'}),
        html.Div([
            html.P(
                id = "podcast_result"

            )
        ])

    ])
    init_callbacks(dash_app)
    return dash_app.server, dash_app

def init_callbacks(dash_app):

    @dash_app.callback(#update available entities for a category
        # Output('available_entities', 'options'),
        Output('podcast_result', 'children'),
        Input('speakers', 'value')
    )
    def update_podcast(guest_name):
        return str(list(collection.find({"guest":guest_name})))
        # queried = collection.find({},{"_id":0, "traits."+category:1})
        # filtered = list(set([ent for doc in queried for ent in doc["traits"][category]]))
        # options = [{'label': i, 'value': i} for i in filtered] #format options for dropdown
        # sorted_options = sorted(options, key = lambda x:x["label"])
        # return sorted_options, sorted_options[0]['value']