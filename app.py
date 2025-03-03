import logging
import threading

from flask import Flask

from router.auth import auth
from router.main import main
from scheduler import run_scheduler
from setup import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask's `app` object
app = Flask(
    __name__,
    instance_relative_config=False,
    template_folder="templates",
    static_folder="static",
)

# Configure App
app.config['SECRET_KEY'] = 'ul7p5cjmkcpeb2bazau'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config["SESSION_PERMANENT"] = False
app.config["SCHEDULER_API_ENABLED"] = True
app.config["SESSION_TYPE"] = "filesystem"

# Blue Printers
app.register_blueprint(auth)
app.register_blueprint(main)

# Init DB
db.init_app(app)
with app.app_context():
    # db.drop_all()
    db.create_all()

if __name__ == '__main__':
    threading.Thread(target=run_scheduler,
                     daemon=True).start()
    app.run(port=9090)
