import os
from flask import Flask
from asgiref.wsgi import WsgiToAsgi
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
asgi_app = WsgiToAsgi(app)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.getcwd()}/todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
