g// ─────────────────────────────────────────────
// Rock Nashville Parking — Backend Server
// ─────────────────────────────────────────────
// This file is the "waiter" between the app and
// the database. It listens for requests from
// browsers and reads/writes reservations.
// ─────────────────────────────────────────────

const express = require('express');   // web server library
const Database = require('better-sqlite3'); // SQLite library
const cors = require('cors');         // allows browsers to talk to this server
const path = require('path');

const app = express();
const PORT = 3000;

// ── Middleware ────────────────────────────────
// These lines tell Express how to handle incoming
// requests before they reach our routes.

app.use(cors());                          // allow cross-origin requests
app.use(express.json());                  // parse JSON request bodies
app.use(express.static('public'));        // serve the index.html from /public

// ── Database setup ────────────────────────────
// This creates a file called parking.db in the
// project folder. If it already exists, it just
// opens it. Think of it like opening a spreadsheet.

const db = new Database('parking.db');

// Create the reservations table if it doesn't exist yet.
// SQL is the language databases speak. This says:
// "Make a table called reservations with these columns,
//  but only if it doesn't already exist."
db.exec(`
  CREATE TABLE IF NOT EXISTS reservations (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    company   TEXT NOT NULL,
    spots     INTEGER NOT NULL,
    start     TEXT NOT NULL,
    end       TEXT,
    contact   TEXT,
    lease     TEXT,
    notes     TEXT,
    created   TEXT DEFAULT (datetime('now'))
  )
`);

console.log('Database ready.');

// ── Routes (API endpoints) ────────────────────
// A "route" is a URL the app can call.
// GET  = read data
// POST = send/save new data
// DELETE = remove data

// GET /api/reservations
// Returns every reservation in the database as JSON.
// The app calls this when it first loads.
app.get('/api/reservations', (req, res) => {
  const rows = db.prepare('SELECT * FROM reservations ORDER BY created DESC').all();
  res.json(rows);
});

// POST /api/reservations
// Saves a new reservation sent from the app.
// req.body contains the data the browser sent.
app.post('/api/reservations', (req, res) => {
  const { company, spots, start, end, contact, lease, notes } = req.body;

  // Basic validation — don't save garbage data
  if (!company || !spots || !start) {
    return res.status(400).json({ error: 'Company, spots, and start date are required.' });
  }

  const stmt = db.prepare(`
    INSERT INTO reservations (company, spots, start, end, contact, lease, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);

  // The ? marks are placeholders — this prevents SQL injection attacks.
  // SQL injection is when someone types malicious code into a form field.
  // Using placeholders means the database treats the input as plain text, never as code.
  const result = stmt.run(company, spots, start, end || null, contact, lease, notes);

  // Send back the newly created reservation (with its new id)
  const newRow = db.prepare('SELECT * FROM reservations WHERE id = ?').get(result.lastInsertRowid);
  res.json(newRow);
});

// DELETE /api/reservations/:id
// Removes a single reservation by its ID.
// The :id is a URL parameter — e.g. DELETE /api/reservations/42
app.delete('/api/reservations/:id', (req, res) => {
  const { id } = req.params;
  db.prepare('DELETE FROM reservations WHERE id = ?').run(id);
  res.json({ success: true });
});

// ── Catch-all ─────────────────────────────────
// For any URL that isn't an API route, serve the
// main index.html. This is what lets the app load
// when someone visits just the IP address.
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ── Start the server ──────────────────────────
// This tells Node to start listening for incoming
// connections on port 3000.
// Port = a numbered "door" on your server.
// Port 3000 is a common dev port. Port 80 = HTTP,
// Port 443 = HTTPS. We'll use 3000 for now.
app.listen(PORT, () => {
  console.log(`Rock Nashville Parking running at http://localhost:${PORT}`);
  console.log('Share your VPS IP address with the team, e.g: http://123.456.78.9:3000');
});
