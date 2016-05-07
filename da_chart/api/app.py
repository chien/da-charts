import os

from flask import Flask
from flask import render_template, send_from_directory
from werkzeug.exceptions import BadRequest

def create_app(testing=False):
    app = Flask(__name__)
    _init_index(app)
    return app

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../www")

def _init_index(app):
    app.add_url_rule('/', 'index', _index)
    app.add_url_rule('/<path:path>', 'static_proxy', _static_proxy)


def _static_proxy(path):
    return send_from_directory(root, path)


def _index():
    return render_template('index.html')
