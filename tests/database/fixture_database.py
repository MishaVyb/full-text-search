import asyncio

import alembic
import pytest
from alembic.config import Config as AlembicConfig
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from models import Base
from settings.settings import Settings, logger
from tests.utils import async_create_database, async_drop_database


@pytest.fixture(scope='session')
def engine(settings: Settings):
    return create_async_engine(settings.DATABASE_URL, echo=settings.SQL_LOGS, echo_pool=settings.SQL_POOL_LOGS)


@pytest.fixture(scope='session')
async def setup_database(engine: AsyncEngine):
    """
    Create test database. Fixture with async implementation of sqlalchemy_utils methods.
    """

    await async_create_database(engine.url)

    logger.debug(f'Successfully set up test database: {engine.url}. ')

    yield

    logger.debug('Tear down all test databases. ')
    async with engine.begin() as conn:
        databases = (await conn.execute(text('SELECT datname FROM pg_database'))).scalars().all()

    for name in databases:
        if 'pytest_' in name:
            await async_drop_database(engine.url.set(database=name))


@pytest.fixture(
    params=[
        pytest.param(dict(CREATE_TABLES_BY_METADATA=True), id='[1] CREATE TABLE BY METADATA'),
        # pytest.param(dict(CREATE_TABLES_BY_METADATA=False), id='[2] CREATE TABLE BY ALEMBIC MIGRATIONS'),
    ]
)
def setup_tables(request: pytest.FixtureRequest, engine: AsyncEngine, setup_database: None):
    """
    If CREATE_TABLES_BY_METADATA, create tables by actual metadata DDL.
    It useful for checking latest changes when alembic revision file is not contains that last changes yet.

    Otherwise, setup tables by running alembic migrations.
    Docs: https://alembic.sqlalchemy.org/en/latest/api/commands.html
    """
    CREATE_TABLES_BY_METADATA = request.param['CREATE_TABLES_BY_METADATA']
    if CREATE_TABLES_BY_METADATA:

        async def _setup():
            async with engine.begin() as connection:
                await connection.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
                await connection.execute(text('CREATE EXTENSION IF NOT EXISTS pg_trgm'))
                await connection.run_sync(Base.metadata.create_all)

        async def _teardown():
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.drop_all)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(_setup())
        yield
        loop.run_until_complete(_teardown())

    else:
        config = AlembicConfig('alembic.ini')
        alembic.command.upgrade(config, 'heads')
        yield
        alembic.command.downgrade(config, 'base')


@pytest.fixture
async def session(setup_tables: None, engine: AsyncEngine):
    async with AsyncSession(engine) as session, session.begin():
        yield session
