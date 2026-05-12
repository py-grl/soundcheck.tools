from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db, Reservation
from datetime import date, time, datetime
import calendar

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dockscheduler.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'f764818ae0cc0b7deef1c3c8b63b34e47c13ae0eb4fc865c4e34fc81281e3cfb'
db.init_app(app)
with app.app_context():
    db.create_all()
    with db.engine.connect() as conn:
        for stmt in [
            'ALTER TABLE reservations ADD COLUMN notes TEXT',
            'ALTER TABLE reservations ADD COLUMN start_date DATE',
            'ALTER TABLE reservations ADD COLUMN end_date DATE',
        ]:
            try:
                conn.execute(db.text(stmt))
                conn.commit()
            except Exception:
                pass
        # Copy old 'date' column into start_date/end_date before dropping it
        try:
            conn.execute(db.text(
                'UPDATE reservations SET start_date = "date", end_date = "date" '
                'WHERE start_date IS NULL'
            ))
            conn.commit()
        except Exception:
            pass
        # Drop the old 'date' column (its NOT NULL constraint breaks new inserts)
        try:
            conn.execute(db.text('ALTER TABLE reservations DROP COLUMN "date"'))
            conn.commit()
        except Exception:
            pass

#routes
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/reservations')
def index():
    reservations = Reservation.query.order_by(Reservation.start_date, Reservation.start_time).all()
    return render_template('index.html', reservations=reservations)

@app.route('/all')
def all_reservations():
    reservations = Reservation.query.order_by(Reservation.start_date, Reservation.start_time).all()
    return render_template('index.html', reservations=reservations)

@app.route('/delete/<int:id>')
def delete_reservation(id):
    reservation = Reservation.query.get_or_404(id)
    db.session.delete(reservation)
    db.session.commit()
    flash('Reservation deleted!')
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_reservation(id):
    reservation = Reservation.query.get_or_404(id)

    if request.method == 'POST':
        reservation.name = request.form['name']
        reservation.company = request.form['company']
        reservation.email = request.form['email']
        reservation.dock_number = request.form['dock_number']
        reservation.dock_type = request.form['dock_type']
        reservation.start_date = date.fromisoformat(request.form['start_date'])
        reservation.end_date = date.fromisoformat(request.form['end_date'])
        reservation.start_time = time.fromisoformat(request.form['start_time'])
        reservation.end_time = time.fromisoformat(request.form['end_time'])
        reservation.notes = request.form.get('notes', '')

        conflict = Reservation.has_conflict(
            reservation.dock_number,
            reservation.start_date,
            reservation.end_date,
            reservation.start_time,
            reservation.end_time,
            exclude_id=reservation.id
        )
        if conflict:
            flash('That dock is already booked during that time!')
            return redirect(url_for('edit_reservation', id=id))

        db.session.commit()
        flash('Reservation edited!')
        return redirect(url_for('index'))
    return render_template('add.html', r=reservation)


@app.route('/add', methods=['GET', 'POST'])
def add_reservation():
    if request.method == 'POST':

        # pull data from the form
        name = request.form['name']
        company = request.form['company']
        email = request.form['email']
        dock_number = request.form['dock_number']
        dock_type = request.form['dock_type']
        start_date = date.fromisoformat(request.form['start_date'])
        end_date = date.fromisoformat(request.form['end_date'])
        start_time = time.fromisoformat(request.form['start_time'])
        end_time = time.fromisoformat(request.form['end_time'])

        #check conflicts before saving
        conflict = Reservation.has_conflict(
            dock_number, start_date, end_date, start_time, end_time
        )

        if conflict:
            flash('That dock is already booked during that time!')
            return redirect(url_for('add_reservation'))

        #NO CONFLICT-CREATE AND SAVE
        notes = request.form.get('notes', '')

        new_reservation = Reservation(
            name=name,
            company=company,
            email=email,
            dock_number=dock_number,
            dock_type=dock_type,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            notes=notes
        )

        db.session.add(new_reservation)
        db.session.commit()

        flash('Reservation added!')
        return redirect(url_for('index'))

    return render_template('add.html')


@app.route('/daily')
def daily_view():
    today = date.today()
    now = datetime.now().time()
    # All reservations that cover today (including multi-day)
    reservations = Reservation.query.filter(
        Reservation.start_date <= today,
        Reservation.end_date >= today
    ).all()

    # Build dock status directory
    dock_status = {}

    all_docks = [
        # Vertical arm
        {'number': '301',  'label': '301',  'type': 'regular'},
        {'number': '302',  'label': '302',  'type': 'regular'},
        {'number': '303',  'label': '303',  'type': 'regular'},
        {'number': '304',  'label': '304',  'type': 'regular'},
        {'number': '305',  'label': '305',  'type': 'regular'},
        {'number': '306A', 'label': '306A', 'type': 'regular'},
        {'number': '306B', 'label': '306B', 'type': 'regular'},
        {'number': '307',  'label': '307',  'type': 'regular'},
        {'number': '308',  'label': '308',  'type': 'regular'},
        {'number': '309',  'label': '309',  'type': 'regular'},
        {'number': '310',  'label': '310',  'type': 'regular'},
        {'number': '311',  'label': '311',  'type': 'regular'},
        # Horizontal arm
        {'number': '312A', 'label': '312A', 'type': 'regular'},
        {'number': '312B', 'label': '312B', 'type': 'regular'},
        {'number': '312C', 'label': '312C', 'type': 'regular'},
        {'number': '313',  'label': '313',  'type': 'regular'},
        {'number': '314',  'label': '314',  'type': 'regular'},
        {'number': '315',  'label': '315',  'type': 'regular'},
        {'number': '316',  'label': '316',  'type': 'regular'},
        {'number': '316B', 'label': '316B', 'type': 'regular'},
        {'number': '317B', 'label': '317B', 'type': 'regular'},
        {'number': '317',  'label': '317',  'type': 'regular'},
        {'number': '318',  'label': '318',  'type': 'regular'},
        {'number': '319',  'label': '319',  'type': 'regular'},
        {'number': '320',  'label': '320',  'type': 'regular'},
        {'number': '321',  'label': '321',  'type': 'regular'},
        {'number': '321B', 'label': '321B', 'type': 'regular'},
        {'number': '322B', 'label': '322B', 'type': 'regular'},
        {'number': '322',  'label': '322',  'type': 'regular'},
        {'number': '323',  'label': '323',  'type': 'regular'},
        {'number': '324',  'label': '324',  'type': 'regular'},
        {'number': '325',  'label': '325',  'type': 'regular'},
        {'number': '326',  'label': '326',  'type': 'regular'},
        {'number': '327',  'label': '327',  'type': 'regular'},
        {'number': '328A', 'label': '328A', 'type': 'regular'},
        {'number': '328B', 'label': '328B', 'type': 'regular'},
        {'number': '328C', 'label': '328C', 'type': 'regular'},
    ]
    # Check each dock against today's reservation
    for dock in all_docks:
        dock_num = dock['number']
        dock_reservations = [r for r in reservations if r.dock_number == str(dock_num)]

        currently_booked = None
        for r in dock_reservations:
            # Multi-day: intermediate days are always occupied
            if r.start_date < today < r.end_date:
                currently_booked = r
                break
            # Arrival day: occupied from start_time onward
            if r.start_date == today and r.end_date > today:
                if now >= r.start_time:
                    currently_booked = r
                    break
            # Departure day: occupied until end_time
            if r.end_date == today and r.start_date < today:
                if now <= r.end_time:
                    currently_booked = r
                    break
            # Single-day: normal time range check
            if r.start_date == today == r.end_date:
                if r.start_time <= now <= r.end_time:
                    currently_booked = r
                    break

        dock_status[dock_num] = {
            'label': dock['label'],
            'type': dock['type'],
            'available': currently_booked is None,
            'reservation': currently_booked,
        }

    return render_template('daily.html',
        dock_status=dock_status,
        all_docks=all_docks,
        today=today,
        now=now
        )

@app.route('/monthly')
@app.route('/monthly/<int:year>/<int:month>')
def monthly(year=None, month=None):
    today = date.today()

    if year is None:
        year = today.year
    if month is None:
        month = today.month

    # Build Calendar Grid
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    # get all reservations that touch this month (including multi-day spans)
    from datetime import date as date_cls, timedelta
    month_start = date_cls(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    month_end = date_cls(year, month, last_day)

    reservations = Reservation.query.filter(
        Reservation.start_date <= month_end,
        Reservation.end_date >= month_start
    ).all()

    # Group by each day in this month that the reservation covers
    res_by_day = {}
    for r in reservations:
        clipped_start = max(r.start_date, month_start)
        clipped_end = min(r.end_date, month_end)
        current = clipped_start
        while current <= clipped_end:
            day = current.day
            if day not in res_by_day:
                res_by_day[day] = []
            res_by_day[day].append(r)
            current += timedelta(days=1)

    # Previous and next month for navigation
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    return render_template('monthly.html',
        cal=cal,
        month_name=month_name,
        year=year,
        month=month,
        res_by_day=res_by_day,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        today=today,
    )


if __name__ == '__main__':
    app.run(debug=True)