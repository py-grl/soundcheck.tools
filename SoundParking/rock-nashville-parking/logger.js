const Database = require('better-sqlite3');
const path = require('path');

const DB_PATH = path.join(__dirname, '..', '..', 'Logger', 'logs.db');

const logDb = new Database(DB_PATH);

logDb.exec(`
  CREATE TABLE IF NOT EXISTS logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL,
    user        TEXT,
    action      TEXT    NOT NULL,
    source      TEXT,
    target_type TEXT,
    target_id   INTEGER,
    detail      TEXT
  )
`);

const _insert = logDb.prepare(`
  INSERT INTO logs (timestamp, user, action, source, target_type, target_id, detail)
  VALUES (?, ?, ?, ?, ?, ?, ?)
`);

function logAction(action, { user = null, source = null, targetType = null, targetId = null, detail = null } = {}) {
  _insert.run(new Date().toISOString(), user, action, source, targetType, targetId, detail);
}

const _selectRecord = logDb.prepare(`
  SELECT id, timestamp, user, action, source, target_type, target_id, detail
  FROM logs
  WHERE target_type = ? AND target_id = ?
  ORDER BY id DESC
  LIMIT ?
`);

// Returns the full change history for one record (newest first).
function getRecordLogs(targetType, targetId, limit = 50) {
  return _selectRecord.all(targetType, targetId, limit);
}

module.exports = { logAction, getRecordLogs };
