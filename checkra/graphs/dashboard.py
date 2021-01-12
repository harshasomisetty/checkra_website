"""Instantiate a Dash app."""
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
        routes_pathname_prefix="/dummy/",
        external_stylesheets=[
            'https://codepen.io/chriddyp/pen/bWLwgP.css'
        ],
    )

    #TODO make graph nodes smaller, make edges further away
    #TODO add links from single podcasts to entity graphs
    
    ent_cats = sorted(list(collection.find_one({},{"traits":1, "_id":0})["traits"].keys()))#get all categories stored in mongo
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
        ], style={'margin':'auto', 'width':'600px', 'padding-bottom':'60px'}),
        
        html.Div(children=[ #graph display
            cyto.Cytoscape(
                id='cytoscape-mentions',
                
                layout={'name': 'concentric', 'componentSpacing':60},
                responsive=True,
                style={'width': '60%', 'height': '600px', 'margin':'auto'},
                stylesheet=[
                    {
                        'selector': 'node',
                        'style': {
                            'content': 'data(label)',
                            'font' : '5px'
                        }
                    },
                    {
                        'selector':'.search',
                        'style': {
                            'background-color':'lightgrey'
                        }
                    },
                    {
                        'selector':'.result',
                        'style': {
                            'background-color':'dimgrey'
                        }
                    }
                ]
            )#end node graph code
        ]),
        html.Div(id='cytoscape-tapNodeData-output'),
        html.P(id='cytoscape-mouseoverNodeData-output')
        
    ])
    init_callbacks(dash_app)

    return dash_app.server, dash_app

 
def init_callbacks(dash_app):

    @dash_app.callback(#update available entities for a category
        Output('available_entities', 'options'),
        Output('available_entities', 'value'),
        Input('entity_category', 'value')
    )
    def update_entities(category):
        queried = collection.find({},{"_id":0, "traits."+category:1})
        filtered = list(set([ent for doc in queried for ent in doc["traits"][category]]))
        options = [{'label': i, 'value': i} for i in filtered] #format options for dropdown
        sorted_options = sorted(options, key = lambda x:x["label"])
        return sorted_options, sorted_options[0]['value']

    @dash_app.callback( #update graph elements
        Output("cytoscape-mentions", "elements"),
        Input('available_entities', 'value'),
        Input('entity_category', 'value')
    )
    def update_graph(value, category):
        category = "traits."+category
        elements = [{'data':{"id":value, 'label':value, 'type':'initial'}, 'classes':'search'}]
        for doc in collection.find({category:value},{"_id":0,"guest":1, "books":1}):
            elements.append({'data':{"id":doc["guest"], 'label':doc["guest"], 'type':'result'}, 'classes':'result'})
            elements.append({'data':{"source":value, 'target':doc["guest"], 'type':'result'}, 'classes':'result'})
        return elements
    
    @dash_app.callback( #redirect to podcast breakdown
        Output('cytoscape-tapNodeData-output', 'children'),
        Input('cytoscape-mentions', 'tapNodeData')\
    )
    def displayTapNodeData(data):
        try:
            if data["type"] !="initial":
                info = list(collection.find({"guest":data["label"]}))[0]
                url = "/podcasts/"+info["guest"]
                return dcc.Location(pathname="/podcasts/"+info["guest"], id="hello")
        except:
            pass
    
    @dash_app.callback( #display side title
        Output('cytoscape-mouseoverNodeData-output', 'children'),
        Input('cytoscape-mentions', 'mouseoverNodeData')
    )
    def displayTapNodeData(data):
        try:
            if data["type"] !="initial":
                title = collection.find_one({"guest":data["id"]},{"_id":0,"title":1})["title"]
                return str(data["label"]+"-"+title)
        except:
            pass
