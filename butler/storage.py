import sqlite3
from pathlib import Path
from contextlib import contextmanager

class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.connect() as c:
            c.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS tasks (
              id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL,
              request TEXT NOT NULL, state TEXT NOT NULL,
              proposal TEXT, error TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS calendar (
              task_id TEXT PRIMARY KEY REFERENCES tasks(id), title TEXT NOT NULL,
              start TEXT NOT NULL, end TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit (
              id INTEGER PRIMARY KEY, task_id TEXT, event TEXT NOT NULL,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS memory (
              id INTEGER PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN
              ('preference','fact','episode','commitment')),
              content TEXT NOT NULL, provenance TEXT NOT NULL,
              confidence REAL CHECK(confidence BETWEEN 0 AND 1),
              valid_from TEXT, valid_until TEXT, supersedes INTEGER REFERENCES memory(id),
              created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS operational_state (
              key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
            PRAGMA user_version=1;
            """)
        Path(path).chmod(0o600)

    @contextmanager
    def connect(self):
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        try:
            with c:
                yield c
        finally:
            c.close()

    def rows(self, table):
        assert table in {'tasks','calendar','audit'}
        with self.connect() as c:
            return [dict(r) for r in c.execute(f"SELECT * FROM {table} ORDER BY rowid DESC")]
