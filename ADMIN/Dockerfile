# Matches the interpreter version you're developing against (Python 3.14).
FROM python:3.14-slim

WORKDIR /app

# Copy just requirements.txt first and install before copying the rest of the code.
# Docker caches each instruction as a layer — as long as requirements.txt doesn't
# change, this pip install layer is reused on every rebuild instead of re-running.
COPY ADMIN/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# ADMIN/app.py reaches out of its own folder for the shared Logger module
# (sys.path.insert(..., '../Logger')) and serves tools-main's static files
# after login (send_from_directory('../tools-main', ...)), so all three
# sibling folders get copied in, preserving that same relative layout.
COPY ADMIN/ ./ADMIN/
COPY Logger/ ./Logger/
COPY tools-main/ ./tools-main/

WORKDIR /app/ADMIN

EXPOSE 5000

# gunicorn instead of `python app.py` / Flask's dev server: app.run(debug=True)
# is single-threaded and reloads on file changes, which is fine for local dev
# but wrong for a container that should stay up under real load and not
# leak stack traces via Flask's debugger.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
