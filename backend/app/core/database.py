from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from app.core.config import SETTINGS


DB_PATH = Path(SETTINGS["database"]["sqlite_path"])


def now_text() -> str:
    return datetime.now().isoformat(timespec="seconds")


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                metadata TEXT,
                created_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS health_profiles (
                user_id TEXT PRIMARY KEY,
                age INTEGER,
                gender TEXT,
                chronic_diseases TEXT,
                allergy_history TEXT,
                medication_history TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS encounters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_id TEXT,
                scene TEXT,
                chief_complaint TEXT,
                risk_level TEXT,
                department TEXT,
                summary TEXT,
                metadata TEXT,
                created_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                department TEXT,
                doctor TEXT,
                doctor_title TEXT,
                visit_date TEXT,
                period TEXT,
                time_slot TEXT,
                status TEXT,
                created_at TEXT
            )
            """
        )
        conn.commit()


def upsert_session(session_id: str, title: str = "医疗问诊会话") -> None:
    ts = now_text()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO sessions(id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at
            """,
            (session_id, title, ts, ts),
        )
        conn.commit()


def add_message(session_id: str, role: str, content: str, metadata: Dict[str, Any] | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages(session_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, json.dumps(metadata or {}, ensure_ascii=False), now_text()),
        )
        conn.commit()


def list_messages(session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content, metadata, created_at FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
    return [
        {
            "role": row["role"],
            "content": row["content"],
            "metadata": json.loads(row["metadata"] or "{}"),
            "created_at": row["created_at"],
        }
        for row in reversed(rows)
    ]


def list_sessions(limit: int = 50) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_encounter(
    session_id: str,
    user_id: str,
    scene: str,
    chief_complaint: str,
    risk_level: str,
    department: str,
    summary: str,
    metadata: Dict[str, Any] | None = None,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO encounters(session_id, user_id, scene, chief_complaint, risk_level, department, summary, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user_id,
                scene,
                chief_complaint,
                risk_level,
                department,
                summary,
                json.dumps(metadata or {}, ensure_ascii=False),
                now_text(),
            ),
        )
        conn.commit()


def list_encounters(user_id: str = "demo_user", days: int = 7) -> List[Dict[str, Any]]:
    since = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM encounters
            WHERE user_id=? AND created_at>=?
            ORDER BY created_at DESC
            """,
            (user_id, since),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["metadata"] = json.loads(item.get("metadata") or "{}")
        result.append(item)
    return result


def add_appointment(payload: Dict[str, Any]) -> int:
    with get_conn() as conn:
        existing = conn.execute(
            """
            SELECT id FROM appointments
            WHERE user_id=? AND department=? AND doctor=? AND visit_date=? AND period=? AND time_slot=? AND status='已预约'
            LIMIT 1
            """,
            (
                payload.get("user_id", "demo_user"),
                payload["department"],
                payload["doctor"],
                payload["visit_date"],
                payload["period"],
                payload["time_slot"],
            ),
        ).fetchone()
        if existing:
            return int(existing["id"])
        cur = conn.execute(
            """
            INSERT INTO appointments(user_id, department, doctor, doctor_title, visit_date, period, time_slot, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("user_id", "demo_user"),
                payload["department"],
                payload["doctor"],
                payload.get("doctor_title", ""),
                payload["visit_date"],
                payload["period"],
                payload["time_slot"],
                "已预约",
                now_text(),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_appointments(user_id: str = "demo_user") -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM appointments
            WHERE user_id=?
            ORDER BY visit_date ASC, period ASC, time_slot ASC, id DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def cancel_appointment(appointment_id: int, user_id: str = "demo_user") -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            """
            UPDATE appointments
            SET status='已取消'
            WHERE id=? AND user_id=? AND status='已预约'
            """,
            (appointment_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0


def appointment_counts(user_id: str = "demo_user") -> Dict[str, int]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT department, doctor, visit_date, period, time_slot, COUNT(*) AS total
            FROM appointments
            WHERE user_id=? AND status='已预约'
            GROUP BY department, doctor, visit_date, period, time_slot
            """,
            (user_id,),
        ).fetchall()
    counts: Dict[str, int] = {}
    for row in rows:
        key = appointment_key(row["department"], row["doctor"], row["visit_date"], row["period"], row["time_slot"])
        counts[key] = int(row["total"])
    return counts


def appointment_key(department: str, doctor: str, visit_date: str, period: str, time_slot: str) -> str:
    return f"{department}|{doctor}|{visit_date}|{period}|{time_slot}"


def clear_session(session_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        conn.commit()


def clear_all() -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM sessions")
        conn.execute("DELETE FROM encounters")
        conn.execute("DELETE FROM appointments")
        conn.commit()
