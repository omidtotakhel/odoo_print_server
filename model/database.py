import logging
from datetime import datetime

from setup import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Model(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)  # Primary key
    create_date = db.Column(db.DateTime, default=datetime.utcnow)
    write_date = db.Column(db.DateTime, default=datetime.utcnow)
    create_uid = db.Column(db.Integer)
    write_uid = db.Column(db.Integer)

    @classmethod
    def create(cls, data):
        try:
            logger.info(f"Create: {cls} {data}")
            record = cls(**data)
            db.session.add(record)
            db.session.commit()
            return record

        except Exception as e:
            logger.info(f"Create Error: {cls} {data} {e}")
            return False
        return True

    @classmethod
    def search(cls, domain={}, limit=False):
        logger.info(f"Search: {cls} {domain}")
        try:
            if limit == 1:
                record = cls.query.filter_by(**domain).first()
            else:
                record = cls.query.filter_by(**domain).all()
        except Exception as e:
            logger.info(f"Search Error: {cls} {domain} {e}")
            return False
        return record

    def write(self, data):
        try:
            logger.info(f"Write: {self} {data}")
            for key, value in data.items():
                setattr(self, key, value)
            db.session.commit()
        except Exception as e:
            logger.info(f"Write Error: {self} {data} {e}")
            return False
        return True

    def unlink(self):
        logger.info(f"Unlink: {self}")
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            logger.info(f"Unlink Error: {self} {e}")
            return False
        return True
