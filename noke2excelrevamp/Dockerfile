FROM python:3.14-slim

WORKDIR /app

COPY noke2excelrevamp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY noke2excelrevamp/ ./noke2excelrevamp/
COPY Logger/ ./Logger/

WORKDIR /app/noke2excelrevamp

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
