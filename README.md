# full-text-search
Full Text Search in PostgreSQL with SQLAlchemy by Trigrams with `pg_trgm` Postgres extension.

For explanation see [WiKi](https://github.com/MishaVyb/full-text-search/wiki/Full-Text-Search-in-PostgreSQL-with-SQLAlchemy).

# FuzzySearchService
Usefull for full-text search on single Table on multiply columns.

```python
search = FuzzySearchService(Article.title, Article.body, ...)
...
result = await session.execute(search('some term we want to find'))
```

### Params

* `similarity_limit`
    Postgres default: `0.3`. For using another value, you must set limit for current session:

```python
await set_similarity_limit(session)
```

* `init_index`: bool | `'index_name'`.
    Call for Index initialization. But it do *not* actually create database index.

### Create Index

```python
Bind.metadata.create_all(engine)  # FuzzySearchService(...) must be called in global context in that case
...
search_service.index.create(engine) # or create directly
```

NOTE. Alembic do not support functional indexes correctly. Add index creation at alembic revision file:

```python
op.create_index(
    search_service.index.name,
    search_service.index.table.name,
    search_service.index.expressions,
    **search_service.index_dialect_kw,
)
```

# MaterializedSearchService
Unlike `FuzzySearchService` implement search on Postgres materialized view. Useful for searching through several related tables on join select. Not nesseccery, but `sqlalchemy_utils.create_materialized_view` recommended for view creation.

```python
full_search_service = MaterializedSearchService(
    view=sqlalchemy_utils.create_materialized_view(
        'full_search_service_view',
        select(User.name, User.email, Article.title, Article.body).join(Article, isouter=True)
        Base.metadata,
    ),
)

await full_search_service.refresh()  # refresh view after any table inserts \ updates
result = await session.execute(full_search_service('some term we want to find'))
```

Instead of columns, view table must be provided. And after every depending tables updates or before every search
query `refresh` method should be called.

### Migrations
View will be created on `Base.metadata.create_all`.
For alembic migration raw SQL might be used (or `alembic_utils` with PGMaterializedView).
