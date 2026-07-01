"""
数据源独立采集脚本约定：

每个脚本文件名为 <slug>.py，位于 scripts/sources/ 目录下。
脚本必须导出以下函数：

    def crawl(session, source_id: int, list_url: str, fetcher) -> dict:
        '''
        返回 {"inserted": int, "skipped": int, "error": str}
        session: SQLAlchemy session
        source_id: sources 表的 id
        list_url: 列表页 URL
        fetcher: BaseFetcher 实例
        '''
"""

import importlib.util
import os
import sys

_SOURCES_DIR = os.path.dirname(os.path.abspath(__file__))


def load_source_script(slug: str):
    path = os.path.join(_SOURCES_DIR, f"{slug}.py")
    if not os.path.exists(path):
        return None

    spec = importlib.util.spec_from_file_location(f"sources.{slug}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"sources.{slug}"] = module
    spec.loader.exec_module(module)

    if not hasattr(module, "crawl"):
        raise AttributeError(f"Source script {slug}.py does not export 'crawl' function")
    return module
