from flask import Flask
from flask_mongoengine import MongoEngine
from flask_mail import Mail

app = Flask(__name__)

app.config.from_object('api.instance.config.Config')

db = MongoEngine()
db.init_app(app)

mail = Mail(app)



