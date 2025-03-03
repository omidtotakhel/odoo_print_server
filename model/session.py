from .database import Model
from setup import db as DB


class ClientSession(Model):
    id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)  # primary keys are required by SQLAlchemy
    client_id = DB.Column(DB.String(100), unique=True)
    scheduler_status = DB.Column(DB.Boolean())

    def update_scheduler_state(self, state):
        """Update the state of a print job by job ID."""
        try:
            self.scheduler_status = state
            DB.session.commit()
            return True
        except Exception as e:
            print("Client Session: Error While updating Status ", e)
            return False

