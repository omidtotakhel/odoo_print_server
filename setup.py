from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy



# Create Flask's `app` object
app = Flask(
    __name__,
    instance_relative_config=False,
    template_folder="templates",
    static_folder="static",
)
app.config['SECRET_KEY'] = 'ul7p5cjmkcpeb2bazau'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'



# Setup session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['TEMPLATES_AUTO_RELOAD'] = True
Session(app)


db = SQLAlchemy()

# initialize DB
db.init_app(app)




