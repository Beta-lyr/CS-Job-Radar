"""执行数据库迁移。等效于 python scripts/migrate.py。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db.migrate import auto_migrate

if __name__ == "__main__":
    auto_migrate()
