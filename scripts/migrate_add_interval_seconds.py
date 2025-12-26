"""Migration script: Add interval_seconds column to tasks table.

This script adds the interval_seconds column to the tasks table
for existing databases. For new databases, the column will be
created automatically by SQLAlchemy's create_all.

Usage:
    python scripts/migrate_add_interval_seconds.py
"""

import sqlite3
import sys
from pathlib import Path


def migrate():
    """Add interval_seconds column to tasks table if it doesn't exist."""
    db_path = Path(__file__).parent.parent / "data" / "autoai.db"

    if not db_path.exists():
        print(f"Database not found at {db_path}")
        print("No migration needed - column will be created on first run.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if tasks table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
    )
    if not cursor.fetchone():
        print("Table 'tasks' does not exist yet.")
        print("No migration needed - column will be created on first run.")
        conn.close()
        return

    # Check if column already exists
    cursor.execute("PRAGMA table_info(tasks)")
    columns = [row[1] for row in cursor.fetchall()]

    if "interval_seconds" in columns:
        print("Column 'interval_seconds' already exists. No migration needed.")
        conn.close()
        return

    # Add the column
    try:
        cursor.execute(
            "ALTER TABLE tasks ADD COLUMN interval_seconds INTEGER"
        )
        conn.commit()
        print("Successfully added 'interval_seconds' column to tasks table.")
    except sqlite3.Error as e:
        print(f"Error adding column: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
