"""
Test full text search on Authors and Articles by MaterializedSearchService.
"""

from pprint import pprint
import pytest
from sqlalchemy.ext.asyncio import AsyncSession


from models import full_search

pytestmark = pytest.mark.anyio


async def test_full_search(seed_database: None, session: AsyncSession):
    await full_search.set_similarity_limit(session)

    print('\n--- [case 1] ---')
    result = (await session.execute(full_search('vybornyy', include_similarity_ratio=True))).all()
    assert result
    pprint(result)

    print('\n--- [case 2] ---')
    result = (await session.execute(full_search('Misha', include_similarity_ratio=True))).all()
    assert result
    pprint(result)

    print('\n--- [case 3] ---')
    result = (await session.execute(full_search('SQL', include_similarity_ratio=True))).all()
    assert result
    pprint(result)

    print('\n--- [case 4] ---')
    result = (await session.execute(full_search('Full Text Search', include_similarity_ratio=True))).all()
    assert result
    pprint(result)
