import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection

# Ensure backend package is importable when running from repo root
CURRENT_DIR = os.path.dirname(__file__)

# Try to add paths where the 'app' package may exist
def _add_path_if_contains_app(path: str) -> None:
    if os.path.exists(os.path.join(path, 'app')) and path not in sys.path:
        sys.path.insert(0, path)

# Case 1: running in container, working dir is /app
_add_path_if_contains_app(os.getcwd())

# Case 2: running from repo root, backend/app exists
REPO_BACKEND = os.path.abspath(os.path.join(CURRENT_DIR, '..', ''))  # backend/
_add_path_if_contains_app(REPO_BACKEND)

# Case 3: project root two levels up
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
_add_path_if_contains_app(PROJECT_ROOT)

from app.db.models import Base  # noqa: E402
from app.db.session import _build_database_url  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# set target metadata for 'autogenerate'
target_metadata = Base.metadata


def get_url() -> str:
    # Prefer DATABASE_URL; fall back to ECS-style discrete vars
    url = os.getenv('DATABASE_URL') or _build_database_url()
    if not url:
        # default to local sqlite memory to avoid crashes (no-op)
        url = 'sqlite://'
    return url


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(get_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
