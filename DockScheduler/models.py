from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

CALENDAR_COLORS = [
    '#e74c3c',
    '#3498db',
    '#9b59b6',
    '#27ae60',
    '#e67e22',
    '#1abc9c',
    '#e91e63',
    '#ff9800',
    '#00bcd4',
    '#8bc34a',
]

DOCK_TYPES = [
    ('regular',  'Regular'),
    ('bus',      'Bus'),
    ('truck',    'Truck'),
    ('closed',   'Closed'),
    ('overlock', 'Overlock'),
    ('utility',  'Utility (Indefinite)'),
]

DOCK_OPTIONS = [
    '301','302','303','304','305','306A','306B','307','308','309','310','311',
    '312A','312B','312C','313','314','315','316','316B','317B','317','318',
    '319','320','321','321B','322B','322','323','324','325','326','327',
    '328A','328B','328C',
]


class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)

    name    = db.Column(db.String(100), nullable=True)
    company = db.Column(db.String(100), nullable=True)
    email   = db.Column(db.String(100), nullable=True)

    dock_number = db.Column(db.String(200), nullable=False)
    dock_type   = db.Column(db.String(100), nullable=False)

    all_day = db.Column(db.Boolean, nullable=False, default=False)
    notes   = db.Column(db.Text, nullable=True)

    start_date = db.Column(db.Date, nullable=False)
    end_date   = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time   = db.Column(db.Time, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def dock_numbers(self):
        return [d.strip() for d in self.dock_number.split(',') if d.strip()]

    @property
    def color(self):
        return CALENDAR_COLORS[self.id % len(CALENDAR_COLORS)]

    @property
    def display_name(self):
        return self.company or self.name or 'Reservation'

    def __repr__(self):
        return f'<Reservation {self.display_name} - Dock {self.dock_number}>'

    @staticmethod
    def has_conflict(dock_numbers, start_date, end_date, start_time, end_time,
                     leeway_minutes=0, exclude_id=None):
        from datetime import timedelta, datetime as dt
        if isinstance(dock_numbers, str):
            dock_numbers = [d.strip() for d in dock_numbers.split(',')]
        dock_set = set(dock_numbers)
        leeway = timedelta(minutes=leeway_minutes)
        new_start = dt.combine(start_date, start_time) - leeway
        new_end   = dt.combine(end_date,   end_time)   + leeway

        query = Reservation.query
        if exclude_id:
            query = query.filter(Reservation.id != exclude_id)

        for r in query.all():
            if not dock_set.intersection(set(r.dock_numbers)):
                continue
            existing_start = dt.combine(r.start_date, r.start_time)
            existing_end   = dt.combine(r.end_date,   r.end_time)
            if new_start < existing_end and new_end > existing_start:
                return True
        return False
