import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from models import full_search
from models.models import ArticleModel, AuthorModel


@pytest.fixture
async def seed_database(engine: AsyncEngine, setup_tables: None):
    async with AsyncSession(engine) as session, session.begin():
        session.add_all(
            [
                AuthorModel(
                    username='vybornyy 1',
                    first_name='Misha',
                    last_name='Vybornyy',
                    articles=[
                        ArticleModel(title='Full Text Search. ', body=''),
                        ArticleModel(title='Full Text Search. ', body='Full Text Search in PostgreSQL by SQLAlchemy'),
                        ArticleModel(title='Imagine', body='Imagine all the people living for today. '),
                    ],
                ),
                AuthorModel(
                    username='vybornyy (no articles)',
                    first_name=None,
                    last_name=None,
                ),
            ]
        )

    async with AsyncSession(engine) as session, session.begin():
        await full_search.refresh(session)
