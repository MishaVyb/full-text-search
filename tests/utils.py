from typing import Any

from sqlalchemy import Select, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import ClauseElement, Executable


def quote(clause: Any):
    """Wrap clause into supported by Postgres quotes."""
    return '"' + str(clause) + '"'


async def async_create_database(url: URL | str, encoding: str = 'utf8', template: str = 'template1'):
    """
    Create Postgres database with `asyncpg` driver using.
    """
    url = make_url(url)
    default_postgres = create_async_engine(
        url.set(database='postgres'), isolation_level='AUTOCOMMIT', echo_pool=False, echo=False
    )
    async with default_postgres.begin() as conn:
        sql = f"CREATE DATABASE {quote(url.database)} ENCODING '{encoding}' TEMPLATE {quote(template)}"
        await conn.execute(text(sql))
    await default_postgres.dispose()


async def async_drop_database(url: URL | str):
    """
    Drop Postgres database with `asyncpg` driver using.
    """
    url = make_url(url)
    default_postgres = create_async_engine(
        url.set(database='postgres'), isolation_level='AUTOCOMMIT', echo_pool=False, echo=False
    )
    async with default_postgres.begin() as conn:
        # Disconnect all users from the database we are dropping.
        version = conn.dialect.server_version_info
        pid_column = 'pid' if (version >= (9, 2)) else 'procpid'
        sql = f'''
            SELECT pg_terminate_backend(pg_stat_activity.{pid_column})
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{url.database}'
            AND {pid_column} <> pg_backend_pid();
            '''
        await conn.execute(text(sql))

        # Drop the database.
        sql = f'DROP DATABASE {quote(url.database)}'
        await conn.execute(text(sql))


class explain(Executable, ClauseElement):  # noqa N801
    """
    Get Postgres query plan for debug and test porpoises.
    Docs: https://github.com/sqlalchemy/sqlalchemy/wiki/Query-Plan-SQL-construct
    """

    inherit_cache = True

    def __init__(self, statement: Select, analyze: bool = False):
        self.statement = statement
        self.analyze = analyze


@compiles(explain, "postgresql")
def pg_explain(element, compiler, **kw):
    text = "EXPLAIN "
    if element.analyze:
        text += "ANALYZE "
    text += compiler.process(element.statement, **kw)

    return text
