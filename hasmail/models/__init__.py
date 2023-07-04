"""Hasmail models."""
# flake8: noqa

from __future__ import annotations

import sqlalchemy as sa
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped

from coaster.sqlalchemy import (
    AppenderQuery,
    BaseMixin,
    BaseNameMixin,
    BaseScopedIdMixin,
    DynamicMapped,
    JsonDict,
    MarkdownColumn,
    ModelBase,
    Query,
    TimestampMixin,
    relationship,
)


class Model(ModelBase, DeclarativeBase):
    """Base for models."""

    __with_timezone__ = True


TimestampMixin.__with_timezone__ = True

db = SQLAlchemy(query_class=Query, metadata=Model.metadata)  # type: ignore[arg-type]
Model.init_flask_sqlalchemy(db)


from .email import *
