from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db, Reservation, CALENDAR_COLORS, DOCK_TYPES, DOCK_OPTIONS
from datetime import date, time, datetime, timedelta
from dotenv import load_dotenv
import calendar
import os

load_dotenv()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dockscheduler.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ['SECRET_KEY']
db.init_app(app)

with app.app_context():
    db.create_all()
    with db.engine.connect() as conn:
        for stmt in [
            'ALTER TABLE reservations ADD COLUMN notes TEXT',
            'ALTER TABLE reservations ADD COLUMN start_date DATE',
            'ALTER TABLE reservations ADD COLUMN end_date DATE',
            'ALTER TABLE reservations ADD COLUMN all_day BOOLEAN NOT NULL DEFAULT 0',
        ]:
            try:
                conn.execute(db.text(stmt))
                conn.commit()
            except Exception:
                pass
        try:
            conn.execute(db.text(
                'UPDATE reservations SET start_date = "date", end_date = "date" '
                'WHERE start_date IS NULL'
            ))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(db.text('ALTER TABLE reservations DROP COLUMN "date"'))
            conn.commit()
        except Exception:
            pass


ALL_DOCKS = [
    {'number': '301',  'label': '301'},
    {'number': '302',  'label': '302'},
    {'number': '303',  'label': '303'},
    {'number': '304',  'label': '304'},
    {'number': '305',  'label': '305'},
    {'number': '306A', 'label': '306A'},
    {'number': '306B', 'label': '306B'},
    {'number': '307',  'label': '307'},
    {'number': '308',  'label': '308'},
    {'number': '309',  'label': '309'},
    {'number': '310',  'label': '310'},
    {'number': '311',  'label': '311'},
    {'number': '312A', 'label': '312A'},
    {'number': '312B', 'label': '312B'},
    {'number': '312C', 'label': '312C'},
    {'number': '313',  'label': '313'},
    {'number': '314',  'label': '314'},
    {'number': '315',  'label': '315'},
    {'number': '316',  'label': '316'},
    {'number': '316B', 'label': '316B'},
    {'number': '317B', 'label': '317B'},
    {'number': '317',  'label': '317'},
    {'number': '318',  'label': '318'},
    {'number': '319',  'label': '319'},
    {'number': '320',  'label': '320'},
    {'number': '321',  'label': '321'},
    {'number': '321B', 'label': '321B'},
    {'number': '322B', 'label': '322B'},
    {'number': '322',  'label': '322'},
    {'number': '323',  'label': '323'},
    {'number': '324',  'label': '324'},
    {'number': '325',  'label': '325'},
    {'number': '326',  'label': '326'},
    {'number': '327',  'label': '327'},
    {'number': '328A', 'label': '328A'},
    {'number': '328B', 'label': '328B'},
    {'number': '328C', 'label': '328C'},
]

V_COORDS = [
    (23.4, 5.3),(25.4,10.5),(25.9,12.2),(26.4,14.0),(27.4,16.1),
    (31.1,28.7),(32.4,30.2),(33.2,32.6),(33.9,34.3),(34.4,35.8),
    (35.3,37.5),(35.9,39.8),
]
H_COORDS = [
    (41.9,37.0),(42.9,37.2),(44.6,37.0),(45.8,37.0),(46.9,37.0),
    (48.1,37.0),(49.2,37.0),(50.2,37.0),(51.6,37.0),(52.5,37.0),
    (53.9,37.1),(56.1,37.0),(57.3,37.0),(58.1,37.0),(59.4,37.0),
    (60.6,37.0),(62.1,37.0),(62.9,37.0),(66.2,37.0),(67.6,37.0),
    (68.6,37.0),(69.7,37.1),(70.9,37.0),(72.4,37.0),(73.2,37.0),
]
V_DOCKS = [d['number'] for d in ALL_DOCKS[:12]]
H_DOCKS = [d['number'] for d in ALL_DOCKS[12:]]


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/reservations')
def index():
    filter_mode = request.args.get('filter', 'all')
    sort_mode   = request.args.get('sort', 'recent')
    today = date.today()

    query = Reservation.query

    if filter_mode == 'today':
        query = query.filter(Reservation.start_date <= today, Reservation.end_date >= today)
    elif filter_mode == 'past':
        query = query.filter(Reservation.end_date < today)
    elif filter_mode == 'upcoming':
        query = query.filter(Reservation.start_date > today)

    if sort_mode == 'old':
        query = query.order_by(Reservation.start_date.asc(), Reservation.start_time.asc())
    elif sort_mode == 'name':
        query = query.order_by(Reservation.name.asc())
    elif sort_mode == 'dock':
        query = query.order_by(Reservation.dock_number.asc())
    elif sort_mode == 'duration':
        reservations = query.all()
        reservations.sort(key=lambda r: (r.end_date - r.start_date).days, reverse=True)
        return render_template('index.html', reservations=reservations,
                               filter_mode=filter_mode, sort_mode=sort_mode)
    else:
        query = query.order_by(Reservation.start_date.desc(), Reservation.start_time.desc())

    reservations = query.all()
    return render_template('index.html', reservations=reservations,
                           filter_mode=filter_mode, sort_mode=sort_mode)


@app.route('/all')
def all_reservations():
    reservations = Reservation.query.order_by(
        Reservation.start_date, Reservation.start_time).all()
    return render_template('index.html', reservations=reservations,
                           filter_mode='all', sort_mode='recent')


@app.route('/delete/<int:id>', methods=['POST'])
def delete_reservation(id):
    reservation = Reservation.query.get_or_404(id)
    db.session.delete(reservation)
    db.session.commit()
    flash('Reservation deleted.')
    return redirect(url_for('index'))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_reservation(id):
    reservation = Reservation.query.get_or_404(id)

    if request.method == 'POST':
        reservation.name    = request.form.get('name')    or None
        reservation.company = request.form.get('company') or None
        reservation.email   = request.form.get('email')   or None

        dock_numbers = request.form.getlist('dock_number')
        if not dock_numbers:
            flash('Please select at least one dock.')
            return redirect(url_for('edit_reservation', id=id))
        reservation.dock_number = ','.join(dock_numbers)

        dock_type = request.form['dock_type']
        reservation.dock_type = dock_type
        all_day = 'all_day' in request.form

        reservation.start_date = date.fromisoformat(request.form['start_date'])

        if dock_type == 'utility':
            reservation.end_date   = date(9999, 12, 31)
            reservation.start_time = time(0, 0)
            reservation.end_time   = time(23, 59)
            reservation.all_day    = True
        else:
            reservation.end_date = date.fromisoformat(request.form['end_date'])
            if all_day:
                reservation.start_time = time(0, 0)
                reservation.end_time   = time(23, 59)
                reservation.all_day    = True
            else:
                reservation.start_time = time.fromisoformat(request.form['start_time'])
                reservation.end_time   = time.fromisoformat(request.form['end_time'])
                reservation.all_day    = False

        reservation.notes = request.form.get('notes', '')

        conflict = Reservation.has_conflict(
            reservation.dock_numbers,
            reservation.start_date, reservation.end_date,
            reservation.start_time, reservation.end_time,
            exclude_id=reservation.id
        )
        if conflict:
            flash('That dock is already booked during that time!')
            return redirect(url_for('edit_reservation', id=id))

        db.session.commit()
        flash('Reservation updated!')
        return redirect(url_for('index'))

    return render_template('add.html', r=reservation,
                           dock_types=DOCK_TYPES, dock_options=DOCK_OPTIONS)


@app.route('/add', methods=['GET', 'POST'])
def add_reservation():
    if request.method == 'POST':
        name    = request.form.get('name')    or None
        company = request.form.get('company') or None
        email   = request.form.get('email')   or None

        dock_numbers = request.form.getlist('dock_number')
        if not dock_numbers:
            flash('Please select at least one dock.')
            return redirect(url_for('add_reservation'))
        dock_number = ','.join(dock_numbers)

        dock_type = request.form['dock_type']
        all_day   = 'all_day' in request.form

        start_date = date.fromisoformat(request.form['start_date'])

        if dock_type == 'utility':
            end_date   = date(9999, 12, 31)
            start_time = time(0, 0)
            end_time   = time(23, 59)
            all_day    = True
        else:
            end_date = date.fromisoformat(request.form['end_date'])
            if all_day:
                start_time = time(0, 0)
                end_time   = time(23, 59)
            else:
                start_time = time.fromisoformat(request.form['start_time'])
                end_time   = time.fromisoformat(request.form['end_time'])

        notes = request.form.get('notes', '')

        conflict = Reservation.has_conflict(
            [d.strip() for d in dock_number.split(',')],
            start_date, end_date, start_time, end_time
        )
        if conflict:
            flash('That dock is already booked during that time!')
            return redirect(url_for('add_reservation'))

        new_res = Reservation(
            name=name, company=company, email=email,
            dock_number=dock_number, dock_type=dock_type,
            all_day=all_day, start_date=start_date, end_date=end_date,
            start_time=start_time, end_time=end_time, notes=notes,
        )
        db.session.add(new_res)
        db.session.commit()
        flash('Reservation added!')
        return redirect(url_for('index'))

    return render_template('add.html', dock_types=DOCK_TYPES, dock_options=DOCK_OPTIONS)


@app.route('/daily')
def daily_view():
    date_str = request.args.get('date')
    if date_str:
        try:
            view_date = date.fromisoformat(date_str)
        except ValueError:
            view_date = date.today()
    else:
        view_date = date.today()

    today    = date.today()
    now_time = datetime.now().time()
    now_dt   = datetime.combine(today, now_time)

    reservations = Reservation.query.filter(
        Reservation.start_date <= view_date,
        Reservation.end_date   >= view_date
    ).all()

    dock_status = {}
    for dock in ALL_DOCKS:
        dock_num = dock['number']
        dock_res = [r for r in reservations if dock_num in r.dock_numbers]

        currently_booked = None
        for r in dock_res:
            if r.dock_type in ('utility', 'closed', 'overlock'):
                currently_booked = r
                break
            if r.all_day:
                currently_booked = r
                break
            if view_date == today:
                start_dt = datetime.combine(view_date, r.start_time) - timedelta(minutes=45)
                end_dt   = datetime.combine(view_date, r.end_time)   + timedelta(minutes=20)
                if start_dt <= now_dt <= end_dt:
                    currently_booked = r
                    break
            else:
                currently_booked = r
                break

        dock_status[dock_num] = {
            'label':       dock['label'],
            'available':   currently_booked is None,
            'reservation': currently_booked,
        }

    prev_date = view_date - timedelta(days=1)
    next_date = view_date + timedelta(days=1)

    v_docks_coords = list(zip(V_DOCKS, V_COORDS))
    h_docks_coords = list(zip(H_DOCKS, H_COORDS))

    return render_template('daily.html',
        dock_status=dock_status,
        v_docks_coords=v_docks_coords,
        h_docks_coords=h_docks_coords,
        today=today,
        view_date=view_date,
        now=now_time,
        prev_date=prev_date,
        next_date=next_date,
    )


@app.route('/monthly')
@app.route('/monthly/<int:year>/<int:month>')
def monthly(year=None, month=None):
    today = date.today()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    cal        = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    month_start = date(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    month_end   = date(year, month, last_day)

    reservations = Reservation.query.filter(
        Reservation.start_date <= month_end,
        Reservation.end_date   >= month_start
    ).all()

    res_colors = {r.id: CALENDAR_COLORS[r.id % len(CALENDAR_COLORS)] for r in reservations}

    res_by_day = {}
    for r in reservations:
        clipped_start = max(r.start_date, month_start)
        clipped_end   = min(r.end_date,   month_end)
        cur = clipped_start
        while cur <= clipped_end:
            res_by_day.setdefault(cur.day, []).append(r)
            cur += timedelta(days=1)

    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    return render_template('monthly.html',
        cal=cal, month_name=month_name, year=year, month=month,
        res_by_day=res_by_day, res_colors=res_colors,
        prev_month=prev_month, prev_year=prev_year,
        next_month=next_month, next_year=next_year,
        today=today,
    )


if __name__ == '__main__':
    app.run(debug=True)
