FROM python:3.14-slim

WORKDIR /app

COPY tools-main/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY tools-main/ ./tools-main/
COPY Logger/ ./Logger/

WORKDIR /app/tools-main

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
