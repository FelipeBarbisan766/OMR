from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "database.db"

# Context variable to track the current database path
_current_db_path: str | Path = DEFAULT_DB_PATH


def set_db_path(path: str | Path) -> None:
    """Set the database path for this session."""
    global _current_db_path
    _current_db_path = path


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path if db_path is not None else _current_db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    set_db_path(db_path)
    with get_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS exams (
                id TEXT PRIMARY KEY,
                class_name TEXT NOT NULL,
                num_questions INTEGER NOT NULL,
                num_choices INTEGER DEFAULT 5,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                class_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(class_id) REFERENCES exams(id)
            );

            CREATE TABLE IF NOT EXISTS answer_keys (
                exam_id TEXT PRIMARY KEY,
                answers TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(exam_id) REFERENCES exams(id)
            );

            CREATE TABLE IF NOT EXISTS exam_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                exam_id TEXT,
                answers TEXT NOT NULL,
                score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(id),
                FOREIGN KEY(exam_id) REFERENCES exams(id)
            );
            """
        )


# CRUD operations for exams
def create_exam(exam_id: str, class_name: str, num_questions: int, num_choices: int = 5) -> dict:
    """Create a new exam."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO exams (id, class_name, num_questions, num_choices)
            VALUES (?, ?, ?, ?)
            """,
            (exam_id, class_name, num_questions, num_choices),
        )
        conn.commit()
    return get_exam(exam_id)


def get_exam(exam_id: str) -> dict | None:
    """Retrieve an exam by ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, class_name, num_questions, num_choices, created_at FROM exams WHERE id = ?",
            (exam_id,),
        ).fetchone()
    return dict(row) if row else None


def list_exams() -> list[dict]:
    """List all exams."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, class_name, num_questions, num_choices, created_at FROM exams ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def delete_exam(exam_id: str) -> None:
    """Delete an exam and all related data."""
    with get_connection() as conn:
        conn.execute("DELETE FROM exam_attempts WHERE exam_id = ?", (exam_id,))
        conn.execute("DELETE FROM answer_keys WHERE exam_id = ?", (exam_id,))
        conn.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
        conn.commit()


# CRUD operations for students
def create_student(student_id: str, name: str, class_id: str | None = None) -> dict:
    """Create a new student."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO students (id, name, class_id) VALUES (?, ?, ?)",
            (student_id, name, class_id),
        )
        conn.commit()
    return get_student(student_id)


def get_student(student_id: str) -> dict | None:
    """Retrieve a student by ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, name, class_id, created_at FROM students WHERE id = ?",
            (student_id,),
        ).fetchone()
    return dict(row) if row else None


def list_students(class_id: str | None = None) -> list[dict]:
    """List students, optionally filtered by class."""
    with get_connection() as conn:
        if class_id:
            rows = conn.execute(
                "SELECT id, name, class_id, created_at FROM students WHERE class_id = ? ORDER BY name",
                (class_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, name, class_id, created_at FROM students ORDER BY name"
            ).fetchall()
    return [dict(row) for row in rows]


def delete_student(student_id: str) -> None:
    """Delete a student and all related data."""
    with get_connection() as conn:
        conn.execute("DELETE FROM exam_attempts WHERE student_id = ?", (student_id,))
        conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()


# CRUD operations for answer keys
def save_answer_key(exam_id: str, answers: str) -> dict:
    """Save or update an answer key for an exam."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO answer_keys (exam_id, answers)
            VALUES (?, ?)
            ON CONFLICT(exam_id) DO UPDATE SET answers = ?
            """,
            (exam_id, answers, answers),
        )
        conn.commit()
    return get_answer_key(exam_id)


def get_answer_key(exam_id: str) -> dict | None:
    """Retrieve an answer key for an exam."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT exam_id, answers, created_at FROM answer_keys WHERE exam_id = ?",
            (exam_id,),
        ).fetchone()
    return dict(row) if row else None


# CRUD operations for exam attempts
def save_exam_attempt(student_id: str, exam_id: str, answers: str, score: float | None = None) -> dict:
    """Save an exam attempt (OMR results)."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO exam_attempts (student_id, exam_id, answers, score)
            VALUES (?, ?, ?, ?)
            """,
            (student_id, exam_id, answers, score),
        )
        conn.commit()
        attempt_id = cursor.lastrowid
    return get_exam_attempt(attempt_id)


def get_exam_attempt(attempt_id: int) -> dict | None:
    """Retrieve an exam attempt by ID."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, student_id, exam_id, answers, score, created_at
            FROM exam_attempts WHERE id = ?
            """,
            (attempt_id,),
        ).fetchone()
    return dict(row) if row else None


def list_exam_attempts(student_id: str | None = None, exam_id: str | None = None) -> list[dict]:
    """List exam attempts, optionally filtered by student or exam."""
    with get_connection() as conn:
        if student_id and exam_id:
            rows = conn.execute(
                """
                SELECT id, student_id, exam_id, answers, score, created_at
                FROM exam_attempts
                WHERE student_id = ? AND exam_id = ?
                ORDER BY created_at DESC
                """,
                (student_id, exam_id),
            ).fetchall()
        elif student_id:
            rows = conn.execute(
                """
                SELECT id, student_id, exam_id, answers, score, created_at
                FROM exam_attempts
                WHERE student_id = ?
                ORDER BY created_at DESC
                """,
                (student_id,),
            ).fetchall()
        elif exam_id:
            rows = conn.execute(
                """
                SELECT id, student_id, exam_id, answers, score, created_at
                FROM exam_attempts
                WHERE exam_id = ?
                ORDER BY created_at DESC
                """,
                (exam_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, student_id, exam_id, answers, score, created_at
                FROM exam_attempts
                ORDER BY created_at DESC
                """
            ).fetchall()
    return [dict(row) for row in rows]
