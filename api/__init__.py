from flask import Flask
from flask_mongoengine import MongoEngine
from flask_mail import Mail

app = Flask(__name__)

# app.config.from_object('api.config')
app.config['MONGODB_SETTINGS'] = {
    'db': 'webchat',
    'host': 'localhost',
    'port': 27017
}

app.config['MAIL_SERVER']= 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = '*****'
app.config['MAIL_PASSWORD'] = '*****'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

db = MongoEngine()
db.init_app(app)

mail = Mail(app)
#uoowmmbzzvjfrxuo


