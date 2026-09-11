FROM python:3.14-slim

WORKDIR /app


COPY DockScheduler/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn


COPY DockScheduler/ ./DockScheduler/
COPY Logger/ ./Logger/
# Logger/identity.py resolves users via a relative path into ADMIN/users.json
# (it's a sibling of Logger/, not of DockScheduler/) — without this, every
# current_user() lookup here silently returns None and everyone appears
# logged out, no matter how valid their session cookie is.
COPY ADMIN/users.json ./ADMIN/users.json

WORKDIR /app/DockScheduler

EXPOSE 5000


CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
