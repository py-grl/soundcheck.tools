FROM python:3.14-slim

WORKDIR /app

COPY SoundParking/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY SoundParking/ ./SoundParking/
COPY Logger/ ./Logger/

WORKDIR /app/SoundParking

EXPOSE 5003

CMD ["gunicorn", "--bind", "0.0.0.0:5003", "app:app"]
