import re
from pathlib import Path

from scripts.export import write_scripts as test_module


def test_db_version():
    """Verify that the bash script contains the expected db version."""
    script_dir = Path(test_module.__file__).parent
    alembic_db_version = test_module.get_current_db_version()
    # search for two lines like SCRIPT_DB_VERSION="805fc8028f39"
    pattern = r"""SCRIPT_DB_VERSION=["']?(?P<version>[^"']*)["']?"""
    with (script_dir / "build_database_archive.sh").open(encoding="utf-8") as f:
        script_db_versions = [
            match.group("version") for line in f if (match := re.match(pattern, line))
        ]
    assert script_db_versions == [alembic_db_version] * 2


def test_get_and_check_queries():
    """Verify that all the tables defined in model.py have been considered."""
    queries = test_module.get_queries()
    test_module.check_queries(queries)
