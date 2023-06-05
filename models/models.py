from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils import create_materialized_view

from models import Base
from services.search_service import FuzzySearchService, MaterializedSearchService


class AuthorModel(Base, kw_only=True):
    __tablename__ = 'authors'

    username: Mapped[str]
    first_name: Mapped[str | None]
    last_name: Mapped[str | None]

    # relations:
    articles: Mapped[list[ArticleModel]] = relationship(
        back_populates='author',
        default_factory=list,
        repr=False,
    )


class ArticleModel(Base, kw_only=True):
    __tablename__ = 'articles'

    title: Mapped[str]
    body: Mapped[str | None]

    # relations:
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(AuthorModel.id), init=False, repr=False)
    author: Mapped[AuthorModel] = relationship(
        back_populates='articles',
        init=False,
        repr=False,
    )


articles_search = FuzzySearchService(
    ArticleModel.title,
    ArticleModel.body,
    similarity_limit=0.01,
    init_index=True,
)


full_search = MaterializedSearchService(
    create_materialized_view(
        'articles_search_view',
        select(
            #
            # Author fields:
            AuthorModel.username,
            AuthorModel.first_name,
            AuthorModel.last_name,
            #
            # Article fields:
            ArticleModel.title,
            ArticleModel.body,
        ).join(
            ArticleModel,
            isouter=True,
        ),
        Base.metadata,
    ),
    similarity_limit=0.01,
    init_index=True,
)
"""Full text search on Authors and Articles. """
