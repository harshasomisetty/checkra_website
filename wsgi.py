from checkra import create_app
from bs4 import BeautifulSoup
from flask import render_template

app, graphs_app, podcasts_app = create_app()


#add multiple routes here so we can add multiple apps


@app.route('/graphs/', defaults={'cat': None, 'ent': None})  # embed dash view in flask
@app.route("/graphs/<cat>/<ent>")
def entity_graphs(cat, ent):
    footer = BeautifulSoup(graphs_app.index(),"html.parser").footer
    return render_template('graphs.html', title='Entity Graphs', footer=footer)


@app.route('/podcasts/', defaults={'podcast': None, 'name': None})  # embed dash view in flask
@app.route('/podcasts/<podcast>/<name>')  # embed dash view in flask
def single_podcasts(podcast, name):
    footer = BeautifulSoup(podcasts_app.index(), "html.parser").footer
    return render_template('podcasts.html', title='Single Podcasts', footer=footer)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('doesnotexist.html'), 404


if __name__ == "__main__":
    app.run(host='0.0.0.0', threaded=True)
