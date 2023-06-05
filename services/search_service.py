from sqlalchemy import Column, ColumnElement, Index, Select, Table, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql._typing import _DDLColumnArgument


class FuzzySearchService:
    """Search service by Trigrams with `pg_trgm` Postgres extension."""

    index_dialect_kw = dict(
        postgresql_using='gin',
        postgresql_ops={'columns': 'gin_trgm_ops'},
    )

    def __init__(
        self,
        *on_columns: Column[str] | InstrumentedAttribute[str] | Column[str | None] | InstrumentedAttribute[str | None],
        similarity_limit: float | None = None,
        init_index: str | bool = False,
    ) -> None:
        """
        Search service by Trigrams with `pg_trgm` Postgres extension.

        ### Usage:

        >>> search = FuzzySearchService(Article.title, Article.body, ...)
        >>> ...
        >>> result = await session.execute(search('some term we want to find'))

        ### Params
        `similarity_limit`: Postgres default: `0.3`. For using another value, you must set limit for current session:

        >>> await set_similarity_limit(session)

        `init_index`: `True` or `'index_name'`.
            Calling for Index initialization. But it do *not* actually create database index.

        ### Create Index

        >>> Bind.metadata.create_all(engine)  # FuzzySearchService(...) must be called in global context in that case
        ...
        >>> search_service.index.create(engine) # or create directly

        NOTE: Alembic do not support functional indexes correctly. Add index creation at alembic migration file:

        >>> op.create_index(
        >>>     search_service.index.name,
        >>>     search_service.index.table.name,
        >>>     search_service.index.expressions,
        >>>     **search_service.index_dialect_kw,
        >>> )

        Issue: https://github.com/sqlalchemy/alembic/issues/676
        """
        self._entities: set[Table] = {column.table for column in on_columns}
        if len(self._entities) > 1:
            raise ValueError(
                'FuzzySearchService supports querying only through *ONE* table. '
                'Use MaterializedSearchService instead. '
            )

        self._columns = on_columns
        self._similarity_limit = similarity_limit

        self.index: Index | None = None
        if init_index:
            self.index = Index(
                init_index if isinstance(init_index, str) else None,
                self.concat_columns(*on_columns).label('columns'),
                **self.index_dialect_kw,  # type: ignore
            )

    @property
    def columns(self):
        return self._columns

    @classmethod
    def concat_columns(cls, *columns: _DDLColumnArgument) -> ColumnElement[str]:
        if not columns:
            raise ValueError('No columns. ')

        joined_columns = func.coalesce(columns[0], '')
        for idx in range(1, len(columns)):
            joined_columns = joined_columns.concat(func.coalesce(columns[idx], ''))  # type: ignore
        return joined_columns

    async def set_similarity_limit(self, session: AsyncSession, limit: float | None = None) -> None:
        """
        Set limit for current database session (engine).
        """
        if limit is None and self._similarity_limit is None:
            raise ValueError('None limit. ')
        await session.execute(select(func.set_limit(text(str(self._similarity_limit)))))

    def __call__(self, term: str, *, order: bool = True, include_similarity_ratio: bool = False) -> Select:
        """
        Search `term` string.
        """
        columns = self.concat_columns(*self.columns)
        entities = self._entities.copy()
        if include_similarity_ratio:
            entities.add(func.similarity(columns, term).label('similarity_ratio'))  # type: ignore

        statement = select(*entities).where(
            columns.self_group().bool_op("%")(term),
        )

        if order:
            statement = statement.order_by(func.similarity(columns, term).desc())

        return statement


class MaterializedSearchService(FuzzySearchService):
    """
    Unlike `FuzzySearchService` implement search on Postgres materialized view. Useful for searching through several
    related tables on join select. Not nesseccery, but `sqlalchemy_utils.create_materialized_view` recommended for view
    creation.

    ### Usage.

    >>> full_search_service = MaterializedSearchService(
    ...     view=sqlalchemy_utils.create_materialized_view(
    ...         'full_search_service_view',
    ...         select(User.name, User.email, Article.title, Article.body).join(Article, isouter=True)
    ...         Base.metadata,
    ...     ),
    ... )

    >>> await full_search_service.refresh()  # refresh view after any table inserts \ updates
    >>> result = await session.execute(full_search_service('some term we want to find'))

    Instead of columns, view table must be provided. And after every depending tables updates or before every search
    query `refresh` method should be called.

    ### Migrations:

    View will be created on `Base.metadata.create_all`.
    For alembic migration raw SQL might be used (or `alembic_utils` with PGMaterializedView).
    """

    def __init__(self, view: Table, *, similarity_limit: float | None = None, init_index: str | bool = False) -> None:
        self.view = view
        super().__init__(
            *self.view.columns,
            similarity_limit=similarity_limit,
            init_index=f'{self.view.name}_trgm_idx' if init_index is True else init_index,
        )

    async def refresh(self, session: AsyncSession, *, concurrently: bool = False) -> None:
        """
        Update materialized view depending on related tables state.
        """
        # Since session.execute() bypasses autoflush, we must manually flush in
        # order to include newly-created/modified objects in the refresh.
        await session.flush()
        await session.execute(
            text(
                'REFRESH MATERIALIZED VIEW {}{}'.format(
                    'CONCURRENTLY ' if concurrently else '',
                    session.bind.engine.dialect.identifier_preparer.quote(self.view.name),
                )
            )
        )
