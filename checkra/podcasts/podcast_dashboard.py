import json
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
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
import time
matplotlib.use("agg")

db = mongo.db
collections = sorted([col for col in db.collection_names()])
speakers = sorted([speak["guest"] for speak in db[collections[0]].find({},{"guest":1})])

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

    dash_app.layout = html.Div([
        dcc.Store( #store individual podcast data
            id = 'data-store',
        ),
        html.Div( #store speaker
            id = 'from-url',
            children = {"url":False},
            style = {'display':'none'}
        ),
        dcc.Location(
            id = 'entry',
            refresh = False
        ),
        html.Div([
            html.Div([
                html.H3(children=
                    "Podcast Breakdowns",
                    style={'text-align':'center', 'padding-bottom':'5px'}
                ),
                html.P(children=
                    "Summaries/visualizations of the podcast and subsections in each podcast in each library. Lists of mentioned entities in the text.",
                    style={'text-align':'center'}
                ),
                html.P(children=
                    "Visit Entity Graphs to find relations to a specific entitity, or choose from the options below ",
                    style={'text-align':'center'}
                ),
                html.P(children=
                    "(Repeated guest names indicates multiple interviews).",
                    style={'text-align':'center', 'padding-bottom':'5px'}
                ),

                html.Div([
                    html.Div([
                        html.H5(children = "Podcast Libraries", style = {"text-align" : 'center'}),
                        dcc.Dropdown(
                            id = "pod-library",
                            options = [
                                {'label':col.replace("_"," "),'value':col.replace("_"," ")} for col in collections
                            ],
                            value = collections[0],
                            style={'text-align':'center', 'width':'400px'}
                        ),
                    ], style = {'display':'flex', 'flex-direction':'column'}),
                    html.Div([
                        html.H5(children = "Podcast Guests", style = {"text-align" : 'center'}),
                        dcc.Dropdown(
                            id = "speakers",
                            # options = [
                            #     {'label': ent, 'value': ent} for ent in speakers
                            # ],
                            # value=speakers[0],
                            style={'text-align':'center', 'width':'400px'}
                        )
                    ], style = {'display':'flex', 'flex-direction':'column'}),
                ], style={'width':'70%','margin':'auto','display':'flex', 'flex-direction':'row', 'justify-content':'space-around', })
            ]),
            # html.Div( #future div for displaying information about where a podcast is from
            #     id = "pod-library-information"
            # )
        ]),
        html.Hr(),
        html.H4(id='podcast-title', style={'text-align':'center','padding-bottom':'10px'}),

        html.Div([
            html.Div([
                html.Div([
                    html.H5(id = "summary-title", style={"text-align":"center"}),
                    html.P(children = "Adjust Slider for Number of Sentences in Summary", style={"text-align":"center"})
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
                    dcc.Loading(
                        id = "summary-loading",
                        type = 'circle',
                        children = [
                            html.P(
                                id = "summary-result",
                                style={'text-align':'center'}
                            ),
                        ]
                    ),
                    html.Div(id = 'summary-id', style={'display':'none'})
                ])
            ], style={'width':'400px'}),

            html.Div([
                html.Div([
                    html.Div([
                        html.H5(children="Timestamp Breakdown", style={"text-align":"center"}),
                        html.P(children="Click a Colored Sub-Section for a Mini-Summary, \nDrag to zoom in, double click to zoom out",style={"text-align":"center"})
                    ]),
                    html.Div([
                        html.Button("Or Reset to Full Podcast Summary", id="reset-summary", style={'text-align':'center'}, className="btn btn-outline-dark btn-sm")
                    ], style={'margin':'auto','display':'flex', 'justify-content':'space-evenly', 'padding-bottom':'5px'}),
                    html.P(id="subtopic-hover",style={'text-align':'center'}),
                    html.Div([
                        dcc.Loading(
                            id = 'timestamps-loading',
                            type = 'circle',
                            children = [
                                dcc.Graph(
                                    id = "timestamps",
                                    clear_on_unhover = True,
                                    config=dict(displayModeBar=False, autosizeable = False), #disable mode bar
                                )
                            ]
                        )
                    ], style={'width':"100%", 'margin':'auto'}),

                ],style={'width':"100%", 'display':'flex', 'flex-direction':'column'})

            ],style={'width':"500px"}),

            html.Div([
                html.Div([
                    html.Div([
                        html.H5(id="wordcloud-title", style={'text-align':'center'}),
                        html.P(children="Automatic Topic Visualization", style={'text-align':'center'}),
                    ]),
                    html.Div([
                        dcc.Loading(
                            id = 'wordcloud-loading',
                            type='circle',
                            children=[
                                html.Img(
                                    id="wordcloud",
                                    style={'margin':'auto'}
                                )
                            ]
                        )
                    ], style={'margin':'auto'})
                ], style={'width':"100%", 'display':'flex', 'flex-direction':'column'})
            ],style={'width':"400px"}),
        ],style={'display':'flex', 'flex-wrap':'wrap', 'justify-content':'space-around'}),

        html.Hr(),
        html.H4("Mentioned Entities", style={'text-align':'center'}),
        html.P("Entities mentioned in podcast, (some may be misplaced)", style={'text-align':'center'}),
        html.Div(
            id = "entities",
            style={'display':'flex', 'flex-wrap':'wrap', 'justify-content':'space-around'}
        )
    ])
    init_callbacks(dash_app)
    return dash_app.server, dash_app

def init_callbacks(dash_app):

    @dash_app.callback(
        Output('pod-library','value'),
        Output('from-url','children'),
        # Output('pod-library-information'),
        Input('entry','pathname')
    )
    def from_url(url):
        url = url.replace("/podcasts/","")
        if url:
            url = url.replace("_"," ").split("/")
            return url[0], url[1] #, db["information"].find({})
        else:
            return collections[0], speakers[0]

    @dash_app.callback(
        Output('speakers','options'),
        Output('speakers','value'),
        Input('pod-library','value'),
        Input('from-url','children')
    )
    def update_library(library, child):
        keys = [context["prop_id"] for context in dash.callback_context.triggered]
        if "from-url.children" in keys:
            docs = list(db[library].find({},{"guest":1}))
            options = sorted([{'label':s["guest"],'value':s["guest"]} for s in docs], key=lambda x: x["label"])
            return options, child
        else:
            docs = list(db[library].find({},{"guest":1}))

            options = sorted([{'label':s["guest"],'value':s["guest"]} for s in docs], key=lambda x:x['label'])
            return options, options[0]["value"]


    @dash_app.callback(#update available entities for a category
        Output('data-store', 'data'),
        Output('timestamps','figure'),
        Output('podcast-title','children'),
        Input('speakers','value'),
        State('pod-library','value'),

    )
    def update_podcast(value, library):
        info = list(db[library].find({"guest":value}))
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
        Output('summary-id', 'children'),
        Input('timestamps', 'clickData'),
        Input('data-store', 'data'),
        Input('sentence-slider', 'value'),
        Input('reset-summary', 'n_clicks'),
        prevent_initial_call=True
    )
    def update_summary(clickData, data, slider, n_clicks):

        try:
            data = json.loads(data)
            changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
            if not clickData or 'reset-summary' in changed_id:
                return str(" ".join(data["summary"][:slider])), "Full Podcast Summary", -1
            else:
                for i in clickData["points"]:
                    if i["y"]!=0:
                        topic = i["curveNumber"]
                        break
                return str(" ".join(data["subtopics"][topic][:slider])), str("Subtopic "+str(topic+1)+" Summary"), topic
        except:
            pass
    @dash_app.callback(
        Output('wordcloud', 'src'),
        Output('wordcloud-title', 'children'),
        Input('data-store', 'data'),
        Input('summary-id', 'children')
    )
    def update_wordcloud(data, topic):
        build_wordcloud = lambda keywords: WordCloud(background_color="white", height=300).generate_from_frequencies(keywords).to_image()
        data = json.loads(data)
        if topic == -1:
            return build_wordcloud(dict(data["keywords"])), "Full Podcast Wordcloud"
        else:
            return build_wordcloud(dict(data["subtopic_keywords"][topic])), str("Subtopic "+str(topic+1)+" Wordcloud")

    @dash_app.callback( #change label when hovering over subtopics
        Output('subtopic-hover','children'),
        Input('timestamps','hoverData'),
        Input('data-store','data')
    )
    def hoverlabel(hoverData,data): #dynamically change label when hovering
        try:
            data = json.loads(data)
            if not hoverData:
                return "Full Podcast (not hovering on a section)"
            else:
                for i in hoverData["points"]:
                    if i["y"]!=0:
                        topic = i["curveNumber"]
                        break
                return str("Hovering on Subtopic "+str(topic+1))
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
            if len(data["traits"][key])>0 and key!="Topics" and "All" not in key:
                div = html.Div([
                        html.H5(key, style={"text-align":"center", 'padding-top':'5px'}),
                        dcc.Textarea(
                            value = "\n".join(sorted(list(set(data["traits"][key])))),
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
        arr[stamps[i]:stamps[i+1]] = i+1
        top_confi.append(arr)
        i+=1
    arr = np.zeros(sent_count)
    arr[stamps[-1]:] = i+1
    top_confi.append(arr)

    return top_confi
