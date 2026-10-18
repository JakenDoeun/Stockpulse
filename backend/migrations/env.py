"""Alembic environment. The database URL comes from app settings (DATABASE_URL), never from alembic.ini."""
from logging.config import fileConfig

from alembic import context

from app import models  # noqa: F401  (registers tables on Base.metadata)
from app.config import get_settings
from app.db import Base, make_engine

config = context.config
connection = config.attributes.get("connection")  # set when tests run migrations programmatically

if config.config_file_name is not None and connection is None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata
OPTIONS = dict(target_metadata=target_metadata, compare_type=True, render_as_batch=True)  # batch: SQLite ALTER support


def run_migrations_offline() -> None:
    context.configure(url=get_settings().database_url, literal_binds=True, **OPTIONS)
    with context.begin_transaction():
        context.run_migrations()


def run_online(conn) -> None:
    context.configure(connection=conn, **OPTIONS)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
elif connection is not None:
    run_online(connection)
else:
    engine = make_engine(get_settings().database_url)
    with engine.connect() as conn:
        run_online(conn)
    engine.dispose()
