"""The connection settings, checked without touching the database.

These run anywhere, even before you have a password. They pin the settings
that keep the app working on Streamlit Community Cloud and keep the class
inside the server's connection limit.
"""

from pathlib import Path

import certifi
import pytest

from dashboard import db


def test_tls_is_verify_full_with_certifi_roots():
    args = db.connect_args()
    assert args["sslmode"] == "verify-full"
    assert args["sslrootcert"] == certifi.where()
    assert Path(args["sslrootcert"]).is_file()


def test_pool_survives_idle_timeout():
    # The server closes a connection left idle for 30 minutes.
    assert db.ENGINE_OPTIONS["pool_pre_ping"] is True
    assert db.ENGINE_OPTIONS["pool_recycle"] < 30 * 60


def test_pool_is_small():
    # Every laptop and every deployed app shares one connection limit.
    assert db.ENGINE_OPTIONS["pool_size"] + db.ENGINE_OPTIONS["max_overflow"] <= 3


def test_engine_from_secrets_builds_url(tmp_path):
    secrets = tmp_path / "secrets.toml"
    secrets.write_text(
        "[connections.db]\n"
        'dialect = "postgresql"\n'
        'driver = "psycopg"\n'
        'host = "example.org"\n'
        "port = 5432\n"
        'database = "vinyl_vault"\n'
        'username = "student"\n'
        'password = "not-a-real-password"\n'
    )
    engine = db.engine_from_secrets(secrets)
    assert engine.url.drivername == "postgresql+psycopg"
    assert engine.url.host == "example.org"
    assert engine.url.database == "vinyl_vault"
    assert engine.pool.size() == db.ENGINE_OPTIONS["pool_size"]
    assert engine.pool.checkedout() == 0  # nothing was opened
    engine.dispose()


def test_missing_secrets_file_says_what_to_do(tmp_path):
    with pytest.raises(FileNotFoundError, match=r"secrets\.toml\.example"):
        db.engine_from_secrets(tmp_path / "secrets.toml")
