import json
import dash
import dash_core_components as dcc
import dash_html_components as html
# import dash_cytoscape as cyto
from dash.dependencies import Input, Output
import dash_table
import numpy as np
import pandas as pd
import math
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
    # print(speakers)
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

            ),
            dcc.Graph(id="timestamps")
        ])

    ])
    init_callbacks(dash_app)
    return dash_app.server, dash_app

def init_callbacks(dash_app):

    @dash_app.callback(#update available entities for a category
        # Output('available_entities', 'options'),
        Output('podcast_result', 'children'),
        Output('timestamps','figure'),
        Input('speakers', 'value')
    )
    def update_podcast(guest_name):
        # return str()
        info = list(collection.find({"guest":guest_name},{'guest':1,"stamps":1,"sent_count":1, "word_count":1,"_id":0}))
        # print(list(info)[0]["sent_count"])
        sent_count = info[0]["sent_count"]
        word_count = info[0]["word_count"]
        stamps = info[0]["stamps"]

        final_topic_confi = stamps_expanded(stamps, sent_count)
        top_confi = np.zeros([int(math.log(word_count)), sent_count]) #2d array of confidences for each topic
        x_vals = np.arange(sent_count)
        # df = pd.DataFrame(top_confi)
        for ind, i in enumerate(final_topic_confi): #set graph
            top_confi[int(i)][ind] = .8
        fig = px.line(x=x_vals, y=[topic for topic in top_confi])
        # print(df)
        return str(sent_count)+" "+str(word_count)+" "+str(len(top_confi)), fig

        # print(stamps.keys())
        # ret_string = ""
        # print(type(name))
        # for key in name:
        #     print(type(key))
        # return str(name)


def stamps_expanded(stamps, sent_count):
    final_topic_confi = np.empty(sent_count)
    i = 0
    while i<len(stamps)-1:#set section of of final topics equal to corressponding timestamp
        final_topic_confi[stamps[i][0]:stamps[i+1][0]] = stamps[i][1] 
        i+=1
    final_topic_confi[stamps[-1][0]:] = stamps[-1][1]
    return final_topic_confi