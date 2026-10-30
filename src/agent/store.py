import sqlite3
import json
from typing import Optional, Dict, Any, List

class JobStore:
    def __init__(self, db_path: str = "research_jobs.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_stage TEXT NOT NULL,
                    logs TEXT,
                    plan TEXT,
                    sources TEXT,
                    final_answer TEXT,
                    error TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

            # Schema migration: check if 'logs' column exists
            cursor = conn.execute("PRAGMA table_info(jobs)")
            columns = [column[1] for column in cursor.fetchall()]
            if "logs" not in columns:
                conn.execute("ALTER TABLE jobs ADD COLUMN logs TEXT")
                conn.commit()

    def _parse_json_field(self, val: Any) -> Any:
        if val is None:
            return None
        if isinstance(val, (dict, list)):
            return val
        try:
            return json.loads(val)
        except Exception:
            return None

    def _format_job_row(self, row: sqlite3.Row) -> Dict[str, Any]:
        row_dict = dict(row)
        logs = self._parse_json_field(row_dict.get("logs"))
        plan = self._parse_json_field(row_dict.get("plan"))
        sources = self._parse_json_field(row_dict.get("sources"))
        final_answer = self._parse_json_field(row_dict.get("final_answer"))

        return {
            "job_id": row_dict.get("job_id"),
            "question": row_dict.get("question"),
            "status": row_dict.get("status"),
            "current_stage": row_dict.get("current_stage"),
            "logs": logs if isinstance(logs, list) else [],
            "plan": plan,
            "sources": sources,
            "final_answer": final_answer,
            "error": row_dict.get("error"),
            "retry_count": row_dict.get("retry_count", 0),
            "updated_at": row_dict.get("updated_at")
        }

    def list_jobs(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
            return [self._format_job_row(row) for row in rows]

    def add_log(self, job_id: str, message: str):
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            if not row:
                return
            formatted = self._format_job_row(row)
            logs = formatted["logs"]
            logs.append(message)
            conn.execute("UPDATE jobs SET logs = ?, updated_at = CURRENT_TIMESTAMP WHERE job_id = ?", (json.dumps(logs), job_id))
            conn.commit()

    def save_job(
        self,
        job_id: str,
        question: str,
        status: str,
        current_stage: str,
        plan: Optional[Dict[str, Any]] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
        final_answer: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        retry_count: int = 0
    ):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO jobs (job_id, question, status, current_stage, plan, sources, final_answer, error, retry_count, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(job_id) DO UPDATE SET
                    status=excluded.status,
                    current_stage=excluded.current_stage,
                    plan=COALESCE(excluded.plan, plan),
                    sources=COALESCE(excluded.sources, sources),
                    final_answer=COALESCE(excluded.final_answer, final_answer),
                    error=excluded.error,
                    retry_count=excluded.retry_count,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                job_id,
                question,
                status,
                current_stage,
                json.dumps(plan) if plan else None,
                json.dumps(sources) if sources else None,
                json.dumps(final_answer) if final_answer else None,
                error,
                retry_count
            ))
            conn.commit()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            if not row:
                return None
            return self._format_job_row(row)
