"""每日定时任务总流程：先自动迁移 -> crawl -> normalize -> stats，一键执行。"""

import subprocess
import sys
import os

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, SCRIPTS_DIR)
from migrate import auto_migrate


def run_script(name: str):
    path = os.path.join(SCRIPTS_DIR, name)
    print(f"\n{'='*60}")
    print(f"  Running: {name}")
    print(f"{'='*60}")
    result = subprocess.run([sys.executable, path], cwd=SCRIPTS_DIR)
    if result.returncode != 0:
        print(f"  FAILED: {name} (exit code {result.returncode})")
        sys.exit(result.returncode)
    print(f"  OK: {name}")


if __name__ == "__main__":
    auto_migrate()
    run_script("seed_sources.py")
    run_script("crawl_daily.py")
    run_script("normalize_jobs.py")
    run_script("generate_daily_stats.py")
    print("\nDaily pipeline completed.")
