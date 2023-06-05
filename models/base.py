import uuid

from sqlalchemy import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    type_annotation_map = {
        dict: JSON,
    }

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default_factory=uuid.uuid4, init=False)


# NOTE:
# Default naming convention for all indexes and constraints
# Docs: https://alembic.sqlalchemy.org/en/latest/naming.html
Base.metadata.naming_convention = {
    'all_column_names': lambda constraint, table: '_'.join(  # type: ignore
        [column.name for column in constraint.columns.values()]
    ),
    'ix': 'ix__%(table_name)s__%(all_column_names)s',
    'uq': 'uq__%(table_name)s__%(all_column_names)s',
    'ck': 'ck__%(table_name)s__%(constraint_name)s',
    'fk': ('fk__%(table_name)s__%(all_column_names)s__' '%(referred_table_name)s'),
    'pk': 'pk__%(table_name)s',
}
