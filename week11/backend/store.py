"""每轮原子提交，避免断线后留下没有 ToolMessage 的工具调用。"""
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from langchain_core.messages import messages_from_dict, messages_to_dict

DB_PATH = os.getenv('AGENT_DB_PATH', str(Path(__file__).with_name('agent_memory.db')))


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    try:
        with conn:
            conn.execute('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, title TEXT NOT NULL, messages TEXT NOT NULL, turns TEXT NOT NULL)')
            yield conn
    finally:
        conn.close()


def create(session_id):
    with connect() as db:
        db.execute('INSERT INTO sessions VALUES (?, ?, ?, ?)', (session_id, '新会话', '[]', '[]'))


def read(session_id):
    with connect() as db:
        row = db.execute('SELECT title, messages, turns FROM sessions WHERE id=?', (session_id,)).fetchone()
    if not row:
        return None
    return {'id': session_id, 'title': row[0], 'messages': messages_from_dict(json.loads(row[1])), 'turns': json.loads(row[2])}


def save(session_id, title, messages, turns):
    with connect() as db:
        db.execute('UPDATE sessions SET title=?, messages=?, turns=? WHERE id=?',
                   (title, json.dumps(messages_to_dict(messages), ensure_ascii=False), json.dumps(turns, ensure_ascii=False), session_id))
