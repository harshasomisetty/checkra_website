from flask import Flask, redirect, url_for, render_template, request, Markup, Blueprint
from flask_assets import Environment
from bs4 import BeautifulSoup

from .extensions import mongo

def page_not_found(e):
    return render_template('doesnotexist.html'), 404

def create_app():
    """Create Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object("config.DevelopmentConfig")
    mongo.init_app(app)

    from .home import home
    from .podcasts import podcasts
    
    with app.app_context():

        app.register_blueprint(home.home_bp)
        app.register_blueprint(podcasts.podcasts_bp, url_prefix="/podcasts")
        app.register_error_handler(404, page_not_found)
        
        from .graphs.dashboard import init_dashboard
        app, dashapp1 = init_dashboard(app)
        
        return app, dashapp1
