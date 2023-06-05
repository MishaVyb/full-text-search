"""
Simple tests for database fixtures. Check postgres service is up and running.
"""

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from models import AuthorModel

pytestmark = pytest.mark.anyio


async def test_setup_database_fixture(setup_database: None, engine: AsyncEngine):
    async with engine.begin() as conn:
        assert 'hello world' == (await conn.execute(text("SELECT 'hello world'; "))).scalar()


async def test_setup_tables_fixture(setup_tables: None, engine: AsyncEngine):
    async with engine.begin() as conn:
        assert [] == (await conn.execute(text(f"SELECT * FROM {AuthorModel.__tablename__}; "))).all()


async def test_session_fixture(session: AsyncSession):
    assert [] == (await session.execute(select(AuthorModel))).all()
