"""数据库迁移管理模块。

每次启动关键脚本前调用 auto_migrate()，自动检查并执行未应用的迁移。
迁移文件按文件名排序，存放在 packages/db/migrations/ 目录下。
"""

import os
import sys

_MIGRATIONS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "packages", "db", "migrations")
)


def _get_engine():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from services.crawler.storage.db import get_engine as _engine_fn

    return _engine_fn()


def _ensure_migrations_table(conn):
    from sqlalchemy import text

    conn.execute(
        text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version     TEXT PRIMARY KEY,
                applied_at  TIMESTAMP NOT NULL DEFAULT now()
            )
        """)
    )
    conn.commit()


def _applied_versions(conn) -> set:
    from sqlalchemy import text

    result = conn.execute(text("SELECT version FROM schema_migrations ORDER BY version"))
    return {row[0] for row in result.fetchall()}


def _migration_files() -> list:
    if not os.path.isdir(_MIGRATIONS_DIR):
        print(f"Migration directory not found: {_MIGRATIONS_DIR}")
        return []
    files = sorted(f for f in os.listdir(_MIGRATIONS_DIR) if f.endswith(".sql"))
    return files


def auto_migrate() -> bool:
    """自动执行所有未应用的迁移。返回 True 表示有迁移执行，False 表示已是最新。"""
    files = _migration_files()
    if not files:
        print("[migrate] No migration files found, skipping.")
        return False

    engine = _get_engine()
    with engine.connect() as conn:
        _ensure_migrations_table(conn)
        applied = _applied_versions(conn)
        conn.commit()

        pending = [f for f in files if f not in applied]
        if not pending:
            print(f"[migrate] All {len(files)} migrations already applied.")
            return False

        print(f"[migrate] Found {len(pending)} pending migration(s): {', '.join(pending)}")
        for f in pending:
            _apply_migration(conn, f)

    print(f"[migrate] {len(pending)} migration(s) applied.")
    return True


def _apply_migration(conn, filename: str):
    from sqlalchemy import text

    filepath = os.path.join(_MIGRATIONS_DIR, filename)
    with open(filepath, encoding="utf-8") as fh:
        sql = fh.read()

    print(f"  -> Applying {filename} ...")
    conn.execute(text("BEGIN"))
    try:
        conn.execute(text(sql))
        conn.execute(
            text("INSERT INTO schema_migrations (version) VALUES (:ver)"),
            {"ver": filename},
        )
        conn.execute(text("COMMIT"))
    except Exception:
        conn.execute(text("ROLLBACK"))
        print(f"  -> FAILED: {filename}")
        raise


if __name__ == "__main__":
    auto_migrate()
