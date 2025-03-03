from setup import db as DB
from .database import Model


class Server(Model):

    id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)  # primary keys are required by SQLAlchemy
    name = DB.Column(DB.String(100), nullable=False)
    identifier = DB.Column(DB.String(100), unique=True, nullable=False)
    location = DB.Column(DB.String(100))
    active = DB.Column(DB.Boolean, default=True)
