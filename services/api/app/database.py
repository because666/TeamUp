from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import Settings
from .sql_store import SqlAlchemyStore
from .store import MemoryStore, Store


def create_database_engine(database_url: str) -> Engine:
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=5,
        max_overflow=5,
        hide_parameters=True,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def create_store(settings: Settings) -> Store:
    if settings.store_backend == "memory":
        return MemoryStore()
    engine = create_database_engine(settings.database_url)
    return SqlAlchemyStore(create_session_factory(engine), engine)
