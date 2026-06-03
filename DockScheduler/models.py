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

DOCK_COLORS = {
    '301A': '#e74c3c',
    '301B': '#e67e22',
    '301C': '#f39c12',
    '302':  '#f1c40f',
    '303':  '#2ecc71',
    '304':  '#1abc9c',
    '305A': '#3498db',
    '305B': '#2980b9',
    '305C': '#9b59b6',
    '305D': '#8e44ad',
    '305E': '#e91e63',
    '305F': '#c0392b',
    '306A': '#ff5722',
    '306B': '#ff9800',
    '307':  '#cddc39',
    '308':  '#8bc34a',
    '309':  '#27ae60',
    '310':  '#00bcd4',
    '311':  '#0097a7',
    '312A': '#5c6bc0',
    '312B': '#7e57c2',
    '312C': '#ab47bc',
    '313':  '#ec407a',
    '314':  '#ef5350',
    '315':  '#ff7043',
    '316':  '#ffa726',
    '316B': '#ffca28',
    '317B': '#d4e157',
    '317':  '#aed581',
    '318':  '#4db6ac',
    '319':  '#4fc3f7',
    '320':  '#42a5f5',
    '321':  '#5c6bc0',
    '321B': '#7986cb',
    '322B': '#ba68c8',
    '322':  '#f06292',
    '323':  '#e57373',
    '324':  '#ff8a65',
    '325':  '#a1887f',
    '326':  '#90a4ae',
    '327':  '#26a69a',
    '328A': '#66bb6a',
    '328B': '#9ccc65',
    '328C': '#26c6da',
}

DOCK_TYPES = [
    ('semi',     'Semi'),
    ('bus',      'Bus'),
    ('boxtruck', 'Box Truck'),
    ('trailer',  'Trailer'),
    ('other',    'Other'),
    ('closed',   'Closed'),
    ('utility',  'Utility (Indefinite)'),
]

DOCK_OPTIONS = [
    '301A','301B','301C','302','303','304',
    '305A','305B','305C','305D','305E','305F',
    '306A','306B','307','308','309','310','311',
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


class CustomMarker(db.Model):
    __tablename__ = 'custom_markers'
    id         = db.Column(db.Integer, primary_key=True)
    label      = db.Column(db.String(100), nullable=False)
    x          = db.Column(db.Float, nullable=False)
    y          = db.Column(db.Float, nullable=False)
    expires_at = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Log(db.Model):
    __tablename__ = 'logs'
    id          = db.Column(db.Integer, primary_key=True)
    timestamp   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    action      = db.Column(db.String(50),  nullable=False)   # create, edit, delete, view, login, logout
    source      = db.Column(db.String(100), nullable=True)    # which app/tool logged this
    target_type = db.Column(db.String(50),  nullable=True)    # reservation, marker, etc.
    target_id   = db.Column(db.Integer,     nullable=True)
    detail      = db.Column(db.Text,        nullable=True)    # human-readable summary

    def __repr__(self):
        return f'<Log {self.action} {self.target_type}:{self.target_id}>'
