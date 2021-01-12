from flask import Blueprint, Flask, redirect, url_for, render_template, request, Markup
from checkra.extensions import mongo
home_bp = Blueprint(
    'home_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

@home_bp.route('/')
def home():
    return render_template("home.html")

@home_bp.route("/about")
def about_page():
    return render_template("about.html")

    
