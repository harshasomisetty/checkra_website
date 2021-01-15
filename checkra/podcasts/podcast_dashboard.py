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
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib
import io
matplotlib.use("agg")

collection = mongo.db.lex

def init_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = dash.Dash(
        server=server,
        routes_pathname_prefix="/podcastsdash/",
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
                "Choose a Name to Explore the Podcast",
                style={'text-align':'center', 'padding-bottom':'5px'}
            ),
            html.Div([
                dcc.Dropdown(
                    id = "speakers",
                    options = [
                        {'label': ent, 'value': ent} for ent in speakers
                    ],
                    value=speakers[0]
                )
            ], style={'width':'300px', 'margin':'auto', 'padding-bottom':'10px'}),
        ]),
        html.H4(id='podcast-title', style={'text-align':'center','padding-bottom':'40px'}),
        html.Div([
            html.Div([
                html.Div([
                    html.H5(id = "summary-title", style={"text-align":"center"}),
                    html.P(children = "Adjust Number of Sentences in Summary", style={"text-align":"center"})
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
                        id = "summary-result",
                        style={'text-align':'center'}
                    ),
                    # html.Div(
                    #     id = 'summary-id',
                    #     style={'display':'none'}
                    # )
                ])
            ], style={'width':'30%'}),
            html.Div([
                html.Div([
                    html.Div([
                        html.H5(children="Topic Breakdown", style={"text-align":"center"}),
                        html.P(children="Click a Colored Sub-Section for a Mini-Summary",style={"text-align":"center"})
                    ]),
                    html.Div([
                        html.Button("Reset to Full Podcast Summary", id="reset-summary", style={'text-align':'center'})
                    ], style={'margin':'auto','display':'flex', 'justify-content':'space-evenly', 'padding-bottom':'5px'}),
                    html.P(id="subtopic-hover",style={'text-align':'center'}),
                    html.Div([
                        dcc.Graph(
                            id = "timestamps", 
                            clear_on_unhover = True,
                            config=dict(displayModeBar=False), #disable mode bar
                        )
                    ], style={'width':"100%", 'margin':'auto'}),
                    
                ],style={'width':"100%", 'display':'flex', 'flex-direction':'column'})
 
            ],style={'width':"40%"}),

            html.Div([
                html.H5(id="wordcloud-title", style={'text-align':'center'}),
                html.P(children="Automatic Topic Visualization", style={'text-align':'center'}),
                html.Img(id="wordcloud")
            ],style={'width':"30%"}),
        ],style={'display':'flex', 'justify-content':'space-between'}),
        html.H4("Mentioned Entities", style={'padding-top':'15px','text-align':'center'}),
        html.Div(
            id = "entities",
            style={'display':'flex', 'flex-wrap':'wrap', 'justify-content':'space-around'}
        ) 
    ])
    init_callbacks(dash_app)
    return dash_app.server, dash_app

def init_callbacks(dash_app):

    @dash_app.callback(#update available entities for a category
        Output('data-store', 'data'),
        Output('timestamps','figure'),
        Output('podcast-title','children'),
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
        
        return dumps(info[0]), fig, str(info[0]["guest"]+" and "+ info[0]["host"]+": "+info[0]["title"])

    @dash_app.callback( #Change loaded summary and wordcloud when clicking on reset button or subtopics
        Output('summary-result', 'children'),
        Output('summary-title','children'),
        Output('wordcloud', 'src'),
        Output('wordcloud-title', 'children'),
        Input('timestamps', 'clickData'),
        Input('data-store', 'data'),
        Input('sentence-slider', 'value'),
        Input('reset-summary', 'n_clicks'),
        prevent_initial_call=True
    )
    def update_summary(clickData, data, slider, n_clicks):
        build_wordcloud = lambda summary: WordCloud(background_color="white", height=250).generate(summary).to_image()

        try:
            data = json.loads(data)
            changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
            if not clickData or 'reset-summary' in changed_id:
                return str(" ".join(data["summary"][:slider])), "Full Podcast Summary", build_wordcloud(" ".join(data["summary"])), "Full Podcast Wordcloud"
            else:
                for i in clickData["points"]:
                    if i["y"]!=0:
                        topic = i["curveNumber"]
                        break
                return str(" ".join(data["subtopics"][topic][:slider])), str("Subtopic "+str(topic+1)+" Summary"), build_wordcloud(" ".join(data["subtopics"][topic])), str("Subtopic "+str(topic+1)+" Wordcloud")
        except:
            pass
    
    @dash_app.callback( #change label when hovering over subtopics
        Output('subtopic-hover','children'),
        Input('timestamps','hoverData'),
        Input('data-store','data')
    )
    def subtopic_label_update(hoverData,data): #dynamically change label when hovering
        try:
            data = json.loads(data)
            if not hoverData:
                return "Currently on Full Podcast"
            else:
                for i in hoverData["points"]:
                    if i["y"]!=0:
                        topic = i["curveNumber"]
                        break
                return str("Current on Subtopic "+str(topic+1))
        except:
            pass

    @dash_app.callback( #update all entities textareas when loading new podcast
        Output('entities', 'children'),
        Input('data-store','data')
    )
    def update_entity_views(data):
        data = json.loads(data)
        children = []
        for key in sorted(data["traits"].keys()):
            if len(data["traits"][key])>1 and key!="Topics" and key!="All Entities": 
                div = html.Div([
                        html.H5(key, style={"text-align":"center", 'padding-top':'5px'}), 
                        dcc.Textarea(
                            value = "\n".join(data["traits"][key]),
                            disabled=True,
                            draggable=False,
                            style={'width':'100%', 'height':'250px', 'text-align':'center'}
                        )], style={'width':'400px'}
                )
                children.append(div)

        return children



def stamps_expanded(sent_count, word_count, stamps): #expand initial stamps into multiple topic arrays
    top_confi =[]
    i = 0
    while i<len(stamps)-1:#set section of of final topics equal to corressponding timestamp
        arr = np.zeros(sent_count)
        arr[stamps[i][0]:stamps[i+1][0]] = i+1 
        top_confi.append(arr)
        i+=1
    arr = np.zeros(sent_count)
    arr[stamps[-1][0]:] = i+1
    top_confi.append(arr)
    
    return top_confi