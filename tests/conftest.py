"""Shared test setup: one database connection for the whole test run.

Tests that need the database ask for the `engine` fixture. When
.streamlit/secrets.toml does not exist yet, those tests are skipped with a
note saying so, and the offline tests still run.
"""

from pathlib import Path

import pytest
from sqlalchemy import text

from dashboard import db

SECRETS = Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"


@pytest.fixture(scope="session")
def engine():
    if not SECRETS.is_file():
        pytest.skip(
            "No .streamlit/secrets.toml yet: copy secrets.toml.example and fill it in"
        )
    eng = db.engine_from_secrets(SECRETS)
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def vinyl_vault_engine(engine):
    """For the template's example tests, which only make sense on vinyl_vault."""
    if engine.url.database != "vinyl_vault":
        pytest.skip("This example runs on vinyl_vault; delete it once you have your own tests")
    return engine


def scalar(engine, sql: str, params: dict | None = None):
    """The single value an independent SQL query returns."""
    with engine.connect() as conn:
        return conn.execute(text(sql), params or {}).scalar_one()
