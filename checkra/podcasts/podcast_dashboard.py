import json
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from bson.json_util import dumps
import dash_table
import numpy as np
import pandas as pd
import math
from flask import redirect, url_for, render_template, request, Markup, Blueprint
from ..extensions import mongo
import plotly.express as px
import plotly.graph_objects as go
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
    #TODO add links from single podcasts to entity graphs
    initial_query = list(collection.find({},{"_id":0,"guest":1}))
    speakers = sorted([pod["guest"] for pod in initial_query])

    dash_app.layout = html.Div([
        dcc.Store(
            id = 'data-store',
            data = dumps(list(collection.find({"guest":speakers[0]})))
        ),
        html.Div([
            html.H3(children=
                "Choose a name to explore the Person's Podcast",
                style={'text-align':'center', 'padding-bottom':'20px'}
            ),
            html.P(children=
                "Currently supporting podcasts by Lex Fridman",
                style={'text-align':'center'}
            ),
            html.Div([
                dcc.Dropdown(
                    id = "speakers",
                    options = [
                        {'label': ent, 'value': ent} for ent in speakers
                    ],
                    value=speakers[0]
                )
            ], style={'width':'300px', 'margin':'auto', 'padding-bottom':'30px'}),
        ]),
        
        html.Div([
            
            html.Div([
                html.Div([
                    html.H5(children="Topic Breakdown", style={"text-align":"center"}),
                    html.P(children="Hover over a section for a summary of that subtopic",style={"text-align":"center"})
                ]),
                html.Div([
                    dcc.Graph(
                        id = "timestamps", 
                        clear_on_unhover = True,
                        config=dict(displayModeBar=False) #disable mode bar
                    )
                ]) 
            ],style={'width':"40%"}),
            html.Div([
                html.Div([
                    html.H5(id = "summary", style={"text-align":"center"}),
                    html.P(children = "Adjust slider to control number of sentences in sumamry", style={"text-align":"center"})
                ]),
                html.Div([
                    dcc.Slider(
                        id='sentence-slider',
                        min=1,
                        max=10,
                        value=1,
                        marks={str(number+1): str(number+1) for number in np.arange(10)},
                        step=None
                    ),
                    html.P(
                        id = "podcast_result"
                    )
                ])
                
            ]
            )],style={'display':'flex'}
        ),

        html.Div(
            id = "entities",
            style={'columnCount': 3}
        ) 
    ])
    init_callbacks(dash_app)
    return dash_app.server, dash_app

def init_callbacks(dash_app):

    @dash_app.callback(#update available entities for a category
        Output('data-store', 'children'),
        Output('timestamps','figure'),
        Input('speakers', 'value')
    )
    def update_podcast(guest_name):
        info = list(collection.find({"guest":guest_name}))
        sent_count, word_count, stamps = info[0]["sent_count"], info[0]["word_count"], info[0]["stamps"]

        top_confi= stamps_expanded(sent_count, word_count, stamps)
        layout = go.Layout(
            autosize=True,
            height = 200
            )
        fig = go.Figure(
            layout=layout
        )
        for ind, topic in enumerate(top_confi):
            fig.add_trace(go.Scatter(x=np.arange(sent_count), y=topic, fill='tozeroy', hoverinfo='none', hovertemplate= None))
        
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False, fixedrange=True, range=[.1,1])
        fig.update_layout(
            annotations=[], 
            overwrite=True, 
            showlegend=False, 
            plot_bgcolor="white", 
            margin=dict(t=0, l=20, r=20, b=20),
            hovermode="x"
        )
        
        return dumps(info[0]), fig

    @dash_app.callback(
        Output('podcast_result', 'children'),
        Output('summary','children'),
        Input('timestamps', 'hoverData'),
        Input('data-store', 'children'),
        Input('sentence-slider', 'value'),
        prevent_initial_call=True
    )
    def update_summary(hoverData, data, slider=3):
        try:
            data = json.loads(data)
            if not hoverData:
                return str(" ".join(data["summary"][:slider])), "Main Summary"
            else:
                for i in hoverData["points"]:
                    if i["y"]!=0:
                        topic = i["curveNumber"]
                        break
                return str(" ".join(data["subtopics"][topic][:slider])), str("Subtopic "+str(topic+1)+" Summary")
        except:
            pass
    @dash_app.callback(
        Output('entities', 'children'),
        Input('data-store','data')
    )
    def add_entity_headers(data):
        data = json.loads(data)[0]
        children = []
        for key in sorted(data["traits"].keys()):
            if len(data["traits"][key])>1 and key!="Topics": 
                div = html.Div([
                        html.H5(key, style={"text-align":"center"}), 
                        dcc.Textarea(
                            value = "\n".join(data["traits"][key]),
                            disabled=True,
                            style={'width':'100%', 'height':'200px', 'text-align':'center'}
                        )]
                )
                children.append(div)

        return children

def stamps_expanded(sent_count, word_count, stamps):
    top_confi =[]
    i = 0
    while i<len(stamps)-1:#set section of of final topics equal to corressponding timestamp
        print(stamps)
        arr = np.zeros(sent_count)
        arr[stamps[i][0]:stamps[i+1][0]] = i+1 
        top_confi.append(arr)
        i+=1
    arr = np.zeros(sent_count)
    arr[stamps[-1][0]:] = i+1
    top_confi.append(arr)
    
    return top_confi

# def find_topic(stamps, i)