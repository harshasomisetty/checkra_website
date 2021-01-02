from flask import redirect, url_for, render_template, request, Markup
from ..extensions import mongo

collection = mongo.db.lex
graphs_bp = Blueprint(
    'graphs_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

@graphs_bp.route("/", methods=[""])
    return render_template("graphs.html")