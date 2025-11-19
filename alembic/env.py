import asyncio
from logging.config import fileConfig
import os
import sys

# Make sure "src" is on python path so "app" package is importable
sys.path.append(os.path.join(os.getcwd(), "src"))

from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Import your metadata object here
# the model file must define `Base` (SQLAlchemy declarative base)
from app.models import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_online():
    connectable = create_async_engine(
        os.getenv("DATABASE_URL"),
        future=True,
        echo=True
    )

    async def do_run():
        async with connectable.connect() as connection:
            await connection.run_sync(do_migrations)

    asyncio.run(do_run())

def do_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    raise RuntimeError("Offline mode not supported.")
else:
    run_migrations_online()




# export $(grep -v '^#' .env | xargs)
# echo $DATABASE_URL

# Run the above commands in order before running the alembic (Every time)

# python3 -m alembic revision --autogenerate -m "create users table"
# Add "python3 -m"