import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.models import initialize_db


class TestModels(unittest.TestCase):
    def test_initialize_db_creates_required_tables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "db.sqlite3"
            initialize_db(db_path)

            with sqlite3.connect(db_path) as conn:
                rows = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                ).fetchall()

            table_names = {row[0] for row in rows}
            self.assertIn("students", table_names)
            self.assertIn("answer_keys", table_names)
            self.assertIn("exam_attempts", table_names)


if __name__ == "__main__":
    unittest.main()
