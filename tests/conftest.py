import uuid

import pytest

from settings import Settings, logger
from settings import settings as app_settings

pytest_plugins = [
    'tests.database.fixture_database',
]


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


@pytest.fixture(scope='session')
def settings():
    # return Settings(POSTGRES_DB=f'pytest_') # XXX
    return Settings(POSTGRES_DB=f'pytest_{uuid.uuid4()}')


@pytest.fixture(scope='session', autouse=True)
def patch_settings(settings: Settings):
    logger.debug(f'Test session runs with: {settings}')
    with pytest.MonkeyPatch.context() as monkeypatch:
        for field in Settings.__fields__:
            monkeypatch.setattr(app_settings, field, getattr(settings, field))
        yield
