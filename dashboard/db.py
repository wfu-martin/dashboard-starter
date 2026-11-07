"""One place for every database connection setting.

The app and the tests both connect through this module, so a number on screen
and the test that proves it always come from the same kind of connection.

Why each setting is what it is:

- TLS (`sslmode=verify-full`). The course server only accepts encrypted
  connections, and verify-full also checks that the server really is the
  course server. Connect by its name, never by an IP address.
- Trusted authorities (`sslrootcert=certifi.where()`). To check the server's
  certificate, the driver needs a list of authorities it trusts. Streamlit
  Community Cloud's Linux image does not give the driver a usable list
  (`sslrootcert=system` fails there with "certificate verify failed"), so the
  app brings its own: the `certifi` package. This works the same on macOS,
  Windows, and Community Cloud.
- `pool_pre_ping=True` and `pool_recycle=1500`. The server closes any
  connection left idle for 30 minutes. A deployed app can sit unused for
  hours; without these, the first click after a quiet spell gets an error.
  Pre-ping tests a connection before using it; recycle retires connections
  after 25 minutes, before the server can close them.
- `pool_size=1`, `max_overflow=2`. Every laptop and every deployed app in the
  class shares one connection limit on the server. Three connections per
  running app is plenty for a dashboard that caches its queries.

The connection details themselves (host, database, user, password) live in
`.streamlit/secrets.toml`, which Git ignores. On Community Cloud, paste the
same text into the app's Secrets box.
"""

import tomllib
from pathlib import Path

import certifi
import sqlalchemy
from sqlalchemy.engine import URL

# The [connections.db] section of .streamlit/secrets.toml.
CONNECTION_NAME = "db"
SECRETS_PATH = Path(".streamlit/secrets.toml")

ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 1500,
    "pool_size": 1,
    "max_overflow": 2,
}


def connect_args() -> dict:
    """Driver settings: encrypted, verified, and labeled on the server."""
    return {
        "sslmode": "verify-full",
        "sslrootcert": certifi.where(),
        "application_name": "dashboard",
    }


def get_connection():
    """The app's connection, created once and shared by every viewer.

    Streamlit reads [connections.db] from secrets.toml (or the Secrets box on
    Community Cloud) and adds the settings above.
    """
    import streamlit as st

    return st.connection(
        CONNECTION_NAME, type="sql", connect_args=connect_args(), **ENGINE_OPTIONS
    )


def get_engine() -> sqlalchemy.Engine:
    """The app's connection pool, for the functions in dashboard.metrics."""
    return get_connection().engine


def engine_from_secrets(path: Path = SECRETS_PATH) -> sqlalchemy.Engine:
    """The same connection, built outside Streamlit, for the tests."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} not found. Copy .streamlit/secrets.toml.example to "
            ".streamlit/secrets.toml and fill in the password."
        )
    settings = tomllib.loads(path.read_text())["connections"][CONNECTION_NAME]
    url = URL.create(
        drivername=f"{settings['dialect']}+{settings['driver']}",
        username=settings["username"],
        password=settings.get("password"),
        host=settings["host"],
        port=int(settings.get("port", 5432)),
        database=settings["database"],
    )
    return sqlalchemy.create_engine(url, connect_args=connect_args(), **ENGINE_OPTIONS)
