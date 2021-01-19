from checkra import create_app
from bs4 import BeautifulSoup
from flask import render_template
import os

app, graphs_app, podcasts_app = create_app()

@app.route('/graphs/', methods=["GET","POST"]) #embed dash view in flask
def entity_graphs():
    footer = BeautifulSoup(graphs_app.index(),"html.parser").footer
    return render_template('graphs.html', title='Entity Graphs', footer=footer)

@app.route('/podcasts/', methods=["GET","POST"]) #embed dash view in flask
def single_podcasts():
    footer = BeautifulSoup(podcasts_app.index(),"html.parser").footer
    return render_template('podcasts.html', title='Single Podcasts', footer=footer)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('doesnotexist.html'), 404

if __name__=="__main__":
    app.run(host='0.0.0.0', threaded=True)