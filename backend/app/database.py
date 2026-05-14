"""Motor SQLAlchemy y generador de sesión (`get_db`)."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

_settings = get_settings()

connect_args: dict[str, object] = {}
if _settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    _settings.database_url,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI: sesión de BD con cierre automático."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
