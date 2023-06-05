import logging
import os
from logging.config import dictConfig
from pathlib import Path
from pprint import pformat

from pydantic import BaseSettings
from sqlalchemy.engine.url import URL

BASEDIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DEBUG: bool = True
    LOG_LEVEL: str = 'DEBUG'

    POSTGRES_HOST: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int

    SQL_LOGS: bool = False
    SQL_POOL_LOGS: bool = False

    @property
    def DATABASE_URL(self) -> URL:  # noqa: N802
        return URL.create(
            drivername='postgresql+asyncpg',
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )

    def __str__(self) -> str:
        return pformat(self.dict())

    class Config:
        env_file = os.path.join(BASEDIR, '.env')
        case_sensitive = True


settings = Settings()
print(settings.DATABASE_URL)
dictConfig(
    {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'fmt': '%(levelprefix)s[%(funcName)s] %(message)s',
            },
        },
        'handlers': {
            'console': {
                'level': settings.LOG_LEVEL,
                'formatter': 'default',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stderr',
            },
        },
        'loggers': {
            'root': {
                'level': settings.LOG_LEVEL,
                'handlers': ['console'],
            }
        },
    }
)

logger = logging.getLogger('root')
