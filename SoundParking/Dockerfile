# This is the live app (Node/Express), not the Flask app.py sitting alongside
# it in this folder — confirmed against the production server, where nginx
# proxies /parking to this exact server.js on port 3000.
FROM node:20-slim

WORKDIR /app

# better-sqlite3 is a native addon and needs to compile during npm install.
RUN apt-get update && apt-get install -y --no-install-recommends python3 make g++ \
    && rm -rf /var/lib/apt/lists/*

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY server.js logger.js ./
COPY public/ ./public/

EXPOSE 3000

CMD ["node", "server.js"]
