from datetime import datetime, timedelta

from setup import db as DB
from .database import Model

"""
'job_type',
'printer_id', 'printer_name', 'raw',
'server_id', 'server_code',
'data',
'report_id',
'report_type',
'attachment_id',
'res_ids',
'res_model'
"""


class ServerJob(Model):
    id = DB.Column(DB.Integer, primary_key=True, unique=True)  # primary keys are required by SQLAlchemy
    job_id = DB.Column(DB.Integer)
    printer_id = DB.Column(DB.Integer)
    printer_name = DB.Column(DB.String)
    server_id = DB.Column(DB.Integer, nullable=False)
    server_code = DB.Column(DB.String, nullable=False)
    data = DB.Column(DB.String)
    job_type = DB.Column(DB.String, nullable=False)
    report_id = DB.Column(DB.Integer)
    report_type = DB.Column(DB.String)
    attachment_id = DB.Column(DB.Integer)
    res_ids = DB.Column(DB.Text)
    res_model = DB.Column(DB.String)
    create_date = DB.Column(DB.DateTime, nullable=False)
    state = DB.Column(DB.String)
    reason = DB.Column(DB.String)
    raw = DB.Column(DB.Boolean)

    @classmethod
    def get_completed_jobs(cls):
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        jobs = cls.query.filter(
            cls.create_date >= seven_days_ago,  # Assuming 'created_at' stores the record timestamp
            cls.state.in_(["done", "error", False])  # Filter by status
        ).all()
        return jobs

    @staticmethod
    def _get_id(record):
        return record[0] if record else None

    @classmethod
    def create_job(cls, payload):
        try:
            job = cls.search(domain={'id': int(payload.get('id')),
                                     'server_code': payload.get('server_code')}, limit=1)
            if job:
                return job

            return cls.create(data=(
                {'id': payload.get("id"),
                 'job_id': payload.get('id'),
                 'job_type': payload.get("job_type"),
                 'printer_id': cls._get_id(payload.get("printer_id")),
                 'printer_name': payload.get('printer_name'),
                 'raw': payload.get('raw'),
                 'server_id': cls._get_id(payload.get("server_id")),
                 'server_code': payload.get("server_code"),
                 'data': payload.get("data"),
                 'report_id': cls._get_id(payload.get("report_id")),
                 'report_type': payload.get("report_type"),
                 'attachment_id': cls._get_id(payload.get("attachment_id")),
                 'res_ids': payload.get("res_ids"),
                 'res_model': payload.get("res_model"),
                 'state': 'pending',
                 'create_date': datetime.strptime(payload.get("create_date"), '%Y-%m-%d %H:%M:%S')}
            ))
        except Exception as e:
            print("Server Job: Error While creating job ", e)
            return False

    def update_job_state(self, new_state, reason=False):
        """Update the state of a print job by job ID."""
        try:
            self.state = new_state
            if reason:
                self.reason = reason
            DB.session.commit()
            return True  # Success
        except Exception as e:
            print("Server Job: Error While updating job ", e)
            return False  # Job not found

    def mark_as_done(self):
        self.update_job_state("done")

    def mark_as_failed(self, reason):
        self.update_job_state("error", reason)
