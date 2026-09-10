FROM python:3.14-slim

WORKDIR /app


COPY DockScheduler/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn


COPY DockScheduler/ ./DockScheduler/
COPY Logger/ ./Logger/

WORKDIR /app/DockScheduler

EXPOSE 5000


CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
