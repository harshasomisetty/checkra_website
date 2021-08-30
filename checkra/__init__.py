from flask import Flask, redirect, url_for, render_template, request, Markup, Blueprint
# from flask_assets import Environment
from bs4 import BeautifulSoup

from .extensions import mongo


def create_app():
    """Create Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object("config.ProductionConfig")
    mongo.init_app(app)
    # assets = Environment()
    # assets.init_app(app)

    from .home import home
    
    with app.app_context():

        app.register_blueprint(home.home_bp)

        # from .assets import compile_static_assets
        
        from .graphs.graph_dashboard import init_dashboard
        app, graph_dashapp = init_dashboard(app)
        from .podcasts.podcast_dashboard import init_dashboard
        app, podcast_dashapp = init_dashboard(app) 
        
        # compile_static_assets(assets)

        return app, graph_dashapp, podcast_dashapp
