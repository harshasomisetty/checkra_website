from flask import Blueprint, render_template

graphy = Blueprint("graphy", __name__, static_folder="static", template_folder="templates")


@graphy.route("/")
def test():
    return render_template("topics.html", topic = "hello")