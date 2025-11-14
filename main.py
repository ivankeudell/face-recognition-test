from flask import Flask

flask_server = Flask(__name__)

@flask_server.route('/')
def hello_world():
		return flask_server.redirect("/static/index.html")
