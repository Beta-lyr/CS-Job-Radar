"""执行数据库迁移初始化。"""

import os
import sys

from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from services.crawler.storage.db import get_engine

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
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(sql))
    print("Migration completed.")


if __name__ == "__main__":
    run_migration()
