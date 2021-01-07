from checkra import create_app
from bs4 import BeautifulSoup
from flask import render_template
import os

app, graphs_app = create_app()

@app.route('/graphs/', methods=["GET","POST"]) #embed dash view in flask
def entity_graphs():
    with open("dash_html.txt", "w+") as w:
        w.write(graphs_app.index())
    footer = BeautifulSoup(graphs_app.index(),"html.parser").footer
    return render_template('graphs.html', title='Entity Graphs', footer=footer)

if __name__=="__main__":
    app.run(host='0.0.0.0', threaded=True)