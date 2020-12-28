from flask import Flask, redirect, url_for, render_template, request, Markup
import urllib.parse
import pymongo
from pymongo import MongoClient
import json
import io
import base64
from bson import json_util
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import math
matplotlib.use("agg")
client = pymongo.MongoClient("mongodb+srv://***REMOVED***:"+urllib.parse.quote("***REMOVED***")+"@cluster0.4pec2.mongodb.net/Checkra?retryWrites=true&w=majority")
db = client["podcasts"]
collection=db["lmini"]


app = Flask(__name__)
app.debug = True

@app.route("/")
def home():
    print(client.db_name)
    return render_template("home.html")

@app.route("/podcasts/<spkr>/detailed")
def detailed(spkr):
    name = spkr.replace("_"," ")
    subtopics = collection.find_one({"guest":name})["subtopics"]
    for i in range(2): #so graph loads properly
        plot = build_topic_plot(name)
    return render_template("detailed_guest.html", summaries = subtopics, topic_plot = plot)

@app.route("/podcasts/<spkr>", methods=["GET", "POST"])
def guest(spkr):
    speaker = spkr
    name = spkr.replace("_"," ")
    info = collection.find_one({"guest":name})
    if request.method == "GET":
        return render_template("guest.html", info = info)
    else:
        return redirect(url_for("detailed", spkr = speaker))

@app.route("/podcasts", methods=["GET", "POST"])
def all_podcasts():
    if request.method == "GET":
        all_speakers = list(collection.find({}))
        guests = []
        for i in all_speakers:
            guests.append(i["guest"])
        
        return render_template("podcasts.html", guests = guests)
    else:
        speaker = request.form["nm"]
        return redirect(url_for("guest", spkr=speaker))

@app.route("/people")
def people_graph():
    return render_template("people.html")

@app.route("/topics")
def topic_graph():
    return render_template("topics.html")

@app.route("/books")
def book_graph():
    return render_template("books.html")

@app.route("/about")
def about_page():
    return render_template("about.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('doesnotexist.html'), 404


def stamps_expanded(stamps, sent_count):
    final_topic_confi = np.empty(sent_count)
    i = 0
    while i<len(stamps)-1:#set section of of final topics equal to corressponding timestamp
        final_topic_confi[stamps[i][0]:stamps[i+1][0]] = stamps[i][1] 
        i+=1
    final_topic_confi[stamps[-1][0]:] = stamps[-1][1]
    
    return final_topic_confi
def build_topic_plot(name):
    word_count = collection.find_one({"guest":name})["word_count"]
    sent_count = collection.find_one({"guest":name})["sent_count"]
    stamps = collection.find_one({"guest":name})["stamps"]

    final_topic_confi = stamps_expanded(stamps, sent_count)
    top_confi = np.zeros([int(math.log(word_count)), sent_count]) #2d array of confidences for each topic
    x_vals = np.arange(sent_count)
    NUM_COLORS = int(math.log(word_count))

    cm = plt.get_cmap('gist_rainbow')
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_prop_cycle('color', [cm(1.*i/NUM_COLORS) for i in range(NUM_COLORS)])
    plt.title("Topic Splits")
    plt.xlabel("Sentence Number")
    plt.xticks(np.arange(0, sent_count, 250))
    plt.ylim(.01,.9)
    ax.set_yticklabels([])
    
    for ind, i in enumerate(final_topic_confi): #set graph
        top_confi[int(i)][ind] = .8
    
    for i in range(int(math.log(word_count))): #graph each topic
        plt.plot(x_vals,top_confi[i], label="Topic: "+str(i))
    
    plt.rcParams['figure.figsize'] = [10, 5]
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    return Markup('<img src="data:image/png;base64,{}" >'.format(plot_url))

if __name__ == "__main__":
    app.run()

