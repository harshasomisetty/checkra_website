from flask import Flask, redirect, url_for, render_template, request, Markup, Blueprint

from .extensions import mongo

def create_app():
    """Create Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_pyfile("../config.py")
    mongo.init_app(app)

    from .home import home
    from .podcasts import podcasts
    
    with app.app_context():

        app.register_blueprint(home.home_bp)
        app.register_blueprint(podcasts.podcasts_bp, url_prefix="/podcasts")
        # print(vars)
        return app


# @app.route("/people")
# def people_graph():
#     return render_template("people.html")

# @app.route("/topics")
# def topic_graph():
#     return render_template("topics.html")

# @app.route("/books")
# def book_graph():
#     return render_template("books.html")
