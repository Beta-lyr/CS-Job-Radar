"""执行数据库迁移初始化。"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "crawler"))

from storage.db import engine

MIGRATION_PATH = os.path.join(
    os.path.dirname(__file__), "..", "packages", "db", "migrations", "001_init.sql"
)


def run_migration():
    if not os.path.exists(MIGRATION_PATH):
        print(f"Migration file not found: {MIGRATION_PATH}")
        sys.exit(1)

    with open(MIGRATION_PATH, encoding="utf-8") as f:
        sql = f.read()

    print("Running migration: 001_init.sql ...")
    with engine.begin() as conn:
        conn.execute(text(sql))
    print("Migration completed.")


from sqlalchemy import text

if __name__ == "__main__":
    run_migration()
