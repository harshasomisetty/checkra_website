import os
from flask import Flask, redirect, url_for, render_template, request, Markup
from .extensions import mongo

def create_app(test_config=None):
    app = Flask(__name__)#one instance, relative to application running
    app.config.from_pyfile("../config.py")
    
    mongo.init_app(app)

    with app.app_context():
        import podcasts.views

    return app
