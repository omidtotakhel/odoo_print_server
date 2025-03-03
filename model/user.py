from setup import db as DB
from .database import Model


class User(Model):

    id = DB.Column(DB.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    username = DB.Column(DB.String(100), unique=True)
    password = DB.Column(DB.String(100))
    db = DB.Column(DB.String(100))
    url = DB.Column(DB.String(100))

    cups_url = DB.Column(DB.String(100))
    cups_port = DB.Column(DB.Integer)
    cups_username = DB.Column(DB.String(100))
    cups_password = DB.Column(DB.String(100))

    active = DB.Column(DB.Boolean, default=True)
