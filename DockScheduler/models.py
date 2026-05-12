from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)

    # who
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)

    # where
    dock_number = db.Column(db.String(100), nullable=False)
    dock_type = db.Column(db.String(100), nullable=False)

    notes = db.Column(db.Text, nullable=True)

    # when
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Reservation {self.name} - Dock{self.dock_number}>'

    @staticmethod
    def has_conflict(dock_number, start_date, end_date, start_time, end_time, leeway_minutes=0, exclude_id=None):
        from datetime import timedelta, datetime

        leeway = timedelta(minutes=leeway_minutes)
        new_start = datetime.combine(start_date, start_time) - leeway
        new_end = datetime.combine(end_date, end_time) + leeway

        query = Reservation.query.filter(Reservation.dock_number == dock_number)
        if exclude_id:
            query = query.filter(Reservation.id != exclude_id)

        for r in query.all():
            existing_start = datetime.combine(r.start_date, r.start_time)
            existing_end = datetime.combine(r.end_date, r.end_time)
            if new_start < existing_end and new_end > existing_start:
                return True
        return False
