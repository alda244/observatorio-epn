from functools import cache

from sqlalchemy import Engine, create_engine

from api.config import database_url


@cache
def engine() -> Engine:
    return create_engine(database_url(), pool_pre_ping=True, connect_args={"connect_timeout": 3})
