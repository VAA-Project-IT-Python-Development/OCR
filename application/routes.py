from application import app
from flask import render_template, url_for

@app.route("/")
def index():
    return render_template("index.html", title="Home Page")
@app.route("/upload", methods=["GET", "POST"])
def upload():
    return render_template("upload.html", title="Home")


@app.route("/decoded", methods=["GET", "POST"])
def decoded():
    return "Hello "