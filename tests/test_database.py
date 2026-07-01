from app.database.repository import normalize_database_url


def test_normalize_managed_postgres_urls_for_psycopg():
    assert (
        normalize_database_url("postgres://user:pass@host/db")
        == "postgresql+psycopg://user:pass@host/db"
    )
    assert (
        normalize_database_url("postgresql://user:pass@host/db")
        == "postgresql+psycopg://user:pass@host/db"
    )


def test_normalize_database_url_preserves_explicit_drivers_and_sqlite():
    psycopg_url = "postgresql+psycopg://user:pass@host/db"
    sqlite_url = "sqlite:///data/research_platform.db"

    assert normalize_database_url(psycopg_url) == psycopg_url
    assert normalize_database_url(sqlite_url) == sqlite_url
