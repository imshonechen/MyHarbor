from sqlalchemy import inspect

from app.database import engine, init_database


def test_core_tables_are_created() -> None:
    init_database()
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    assert {"site", "site_config", "site_status_log", "visit_log", "visit_stats"}.issubset(table_names)


def test_cascade_foreign_keys_are_defined() -> None:
    init_database()
    inspector = inspect(engine)

    status_log_fks = inspector.get_foreign_keys("site_status_log")
    visit_log_fks = inspector.get_foreign_keys("visit_log")
    visit_stats_fks = inspector.get_foreign_keys("visit_stats")

    assert status_log_fks and status_log_fks[0]["options"].get("ondelete") == "CASCADE"
    assert visit_log_fks and visit_log_fks[0]["options"].get("ondelete") == "CASCADE"
    assert visit_stats_fks and visit_stats_fks[0]["options"].get("ondelete") == "CASCADE"

