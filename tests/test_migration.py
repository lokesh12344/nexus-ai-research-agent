import pytest
import sqlite3
import os
import json
from src.agent.store import JobStore

def test_legacy_schema_migration():
    db_path = "legacy_test.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    # 1. Create legacy schema
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE jobs (
            job_id TEXT PRIMARY KEY,
            question TEXT NOT NULL,
            status TEXT NOT NULL,
            current_stage TEXT NOT NULL,
            plan TEXT,
            sources TEXT,
            final_answer TEXT,
            error TEXT,
            retry_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("INSERT INTO jobs (job_id, question, status, current_stage) VALUES ('j1', 'q1', 'running', 'planning')")
    conn.commit()
    conn.close()

    # 2. Run JobStore, it should migrate
    store = JobStore(db_path=db_path)

    # 3. Verify migration
    job = store.get_job('j1')
    assert job is not None
    assert "logs" in job
    assert job["logs"] == []

    # 4. Verify adding log
    store.add_log('j1', 'test log')
    job = store.get_job('j1')
    assert job["logs"] == ['test log']

    if os.path.exists(db_path):
        os.remove(db_path)

def test_repeated_initialization():
    db_path = "repeat_test.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    JobStore(db_path=db_path)
    JobStore(db_path=db_path) # Should not raise error

    if os.path.exists(db_path):
        os.remove(db_path)
