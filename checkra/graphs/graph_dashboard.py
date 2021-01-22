import json
from bson.json_util import dumps
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
from collections import Counter

db = mongo.db
collections = sorted([col for col in db.collection_names()])
cyto.load_extra_layouts()

def init_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = dash.Dash(
        server=server,
        routes_pathname_prefix="/graphsdash/",
        external_stylesheets=[
            'https://codepen.io/chriddyp/pen/bWLwgP.css'
        ],
    )

    #TODO make graph nodes smaller, make edges further away
    
    ent_cats = sorted(list(db[collections[0]].find_one({},{"traits":1, "_id":0})["traits"].keys())+["All Keywords"])#get all categories stored in mongo
    dash_app.layout = html.Div([
        dcc.Store(
            id = 'data-store',
        ),
        dcc.Location(
            id = 'entry',
            refresh = False
        ),
        html.Div( #store speaker
            id = 'from-url',
            children = {"url":False},
            style = {'display':'none'}
        ),
        html.H3(
            children="Entity Graphs",
            style={'text-align':'center', 'padding-bottom':'10px'}
        ),
        html.P(
            children="Choose an Entity Category and an available entity to see mentions by Podcast Guests. The default 'All Entities' category displays a graph of all the entities mentioned in all podcasts",
            style={'text-align':'center'}
        ),
        html.P(
            children="The 'All Topics' category lists frequent keywords. Some keywords are noise, but others words like 'Bitcoin' give better specific results where Bitcoin is a major topic in a podcast",
            style={'text-align':'center'}
        ),
        html.Div(
            children=[ #options
                html.Div(children=[
                    html.H6(children = "Entity Category", style = {'text-align':'center', 'padding-above':'9px'}),
                    dcc.Dropdown(
                        id = "entity_category",
                        style = {'text-align':'center'},
                        options = [
                            {'label': ent, 'value': ent} for ent in ent_cats
                        ],
                        # value = ent_cats[0] 
                    )
                ], style={'display': 'inline-block','width':'200px'}),
                html.Div(children=[
                    html.H6(children = "Mentioned Entities", style = {'text-align':'center'}),
                    dcc.Dropdown(
                        id = "available_entities",
                        style = {'text-align':'center'}
                    )
                ], style={'display': 'inline-block','width':'400px', 'padding-left':'30px'}),
            ], 
            style={'margin':'auto', 'width':'600px', 'padding-below':'30px'}
        ),
        html.Div([
            html.Button("Bitcoin Demo", id="bitcoin-demo", style={'text-align':'center'}, className="btn btn-outline-dark btn")
        ], style={'margin':'auto','display':'flex', 'justify-content':'center',}),
        # html.P(id='cytoscape-mouseoverNodeData-output', children="test"),

        html.Hr(), 

        html.Div(id='cytoscape-tapNodeData-output'),
        html.Div(children=[
            html.Div(children=[ #graph display
                html.H4(id = "cytoscape-title", style={"text-align":"center"}),
                html.P(children="The blue circle is the selected entity, red circles are the people who mentioned the blue node. ", style = {'text-align':'center'}),
                
                html.P(children="Zoom in and out for details, drag people circles around, and click a person to go to their podcast breakdown", style = {'text-align':'center'}),
                dcc.Loading(
                    id = "graph-loading",
                    type = 'graph',
                    children = [
                        cyto.Cytoscape(
                            id='cytoscape-mentions',
                            layout={'name': 'cola', 'componentSpacing':200},
                            responsive=True,
                            style={'width': '100%', 'height': '900px'},
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
                                        'background-color':'#0099cc'
                                    }
                                },
                                {
                                    'selector':'.result',
                                    'style': {
                                        'background-color':'#ff6666'
                                    }
                                }
                            ]
                        )#end node graph code
                    ]
                ),
            ], style={'width':'70%'}),

            html.Div(children=[
                html.H4(id='entity-list-title', style={'text-align':'center'}),
                html.P(children="List of all people who mentioned the entity"),
                html.P(children="Repeated names = Multiple podcasts"),
                dcc.Textarea(
                    id = 'entity-list-area',
                    style = {'width':'100%', 'height':'900px', 'text-align':'center'}
                )
            ], style={'width':'20%','text-align':'center'})
        ], style={'display':'flex', 'flex-wrap':'wrap', 'justify-content':'space-around'}),
        
    ])
    init_callbacks(dash_app)

    return dash_app.server, dash_app

 
def init_callbacks(dash_app):
    @dash_app.callback(
        Output('entity_category','value'),
        Output('from-url','children'),
        Input('entry','pathname')
    )
    def from_url(url):
        url = url.replace("/graphs/","")
        if url:
            url = url.replace("_"," ").split("/")
            return url[0].title(), url[1].title() #, db["information"].find({})
        else:
            return collections[0], speakers[0] 

    @dash_app.callback(#update available entities for a category
        
        Output('available_entities', 'options'),
        Output('available_entities', 'value'),
        Output('data-store', 'data'),
        Input('entity_category', 'value'),
        Input('from-url','children')
    )
    def update_entities(category, child):
        all_docs = []
        keys = [context["prop_id"] for context in dash.callback_context.triggered]
        print(keys)
        if category == "All Keywords":
            for collection in db.collection_names():
                for doc in list(db[collection].find({},{"_id":0, "keywords":1, "guest":1})):
                    all_docs.append([np.array(doc["keywords"])[:,0][:20], doc["guest"], str(collection)])
        else:
            for collection in db.collection_names():
                for doc in list(db[collection].find({},{"_id":0, "traits."+category:1, "guest":1})):
                    all_docs.append([list(doc["traits"][category]), doc["guest"], str(collection)])

        all_ents = ([ent for doc in all_docs for ent in doc[0] if ent!="Kashyap"])
        ent_count = Counter(all_ents)
        filtered = [tup[0] for tup in ent_count.most_common(len(ent_count)-1)]
        options = [{'label': i, 'value': i} for i in filtered] #format options for dropdown
        if "from-url.children" in keys:
            return options, child, dumps(all_docs)
        else:
            return options, options[0]['value'], dumps(all_docs) #all_docs is a list of sublists, each sublist contains a list of entities, guest name, and podcast name


    @dash_app.callback( #update graph elements
        Output("cytoscape-mentions", "elements"),
        Output('cytoscape-title',"children"),
        Output('entity-list-title','children'),
        Output('entity-list-area','value'),
        Input('available_entities', 'value'),
        Input('entity_category', 'value'),
        Input('data-store','data')
    )
    def update_graph(value, category, data):
        data = json.loads(data)
        elements = [{'data':{"id":value, 'label':value, 'type':'initial'}, 'classes':'search'}]
            
        mentions = []

        for tup in data:
            if value in tup[0]:
                elements.append({'data':{"id":tup[1], 'label':tup[1], 'type':'result '+tup[2]}, 'classes':'result'})
                elements.append({'data':{"source":value, 'target':tup[1], 'type':'result'}, 'classes':'result'})
                mentions.append(tup[1])
        return elements, 'Mentions Graph of "'+str(value)+'"', 'Mentions List of "'+str(value)+'"', "\n".join(sorted(mentions))
    
    @dash_app.callback(
        Output('entry','pathname'),
        Input('bitcoin-demo','n_clicks')
    )
    def bitcoin_demo(click):
        return "/graphs/all_keywords/bitcoin"
    # @dash_app.callback( #display side title
    #     # Output('cytoscape-mouseoverNodeData-output', 'children'),
    #     Output('')
    #     Input('cytoscape-mentions', 'mouseoverNodeData')
    # )
    # def displayHoverNodeData(data):

    #     # print(data, "hover")
    #     try:
    #         if data["type"] != "initial":
    #             title = collection.find_one({"guest":data["id"]},{"_id":0,"title":1})["title"]
    #             return str(data["label"]+"-"+title)
    #     except:
    #         pass

    @dash_app.callback( #redirect to podcast breakdown
        Output('cytoscape-tapNodeData-output', 'children'),
        Input('cytoscape-mentions', 'tapNodeData')
    )
    def displayClickNodeData(data):
        try:
            if data["type"] !="initial":
                url = "/podcasts/"+ data["type"].replace("result ","").replace(" ", "_")+"/"+data["id"].replace(" ","_")
                return dcc.Location(pathname=url, id="hello")
        except:
            pass