from ararat.db.connection import get_engine_urls


def test_get_engine_urls():
    urls = list(get_engine_urls("postgresql+asyncpg://postgres:pgpassword@127.0.0.1:5432"))
    assert urls == ["postgresql+asyncpg://postgres:pgpassword@127.0.0.1:5432"]

    urls = list(get_engine_urls("postgresql+asyncpg://postgres:pgpassword@?host=127.0.0.1:5432"))
    assert urls == ["postgresql+asyncpg://postgres:pgpassword@127.0.0.1:5432"]

    urls = list(
        get_engine_urls("postgresql+asyncpg://postgres:pgpassword@?host=127.0.0.1:5432&host=127.0.0.1:5433&some=1")
    )
    assert len(urls) == 2
    assert urls[0] == "postgresql+asyncpg://postgres:pgpassword@127.0.0.1:5432?some=1"
    assert urls[1] == "postgresql+asyncpg://postgres:pgpassword@127.0.0.1:5433?some=1"
