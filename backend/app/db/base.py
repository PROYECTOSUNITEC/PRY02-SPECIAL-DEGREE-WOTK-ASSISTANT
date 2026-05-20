"""Base declarativa SQLAlchemy 2.0."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base para todos los modelos ORM."""
