import asyncio
from contextvars import ContextVar
from functools import wraps
from typing import Callable, Optional, TypeVar
from uuid import uuid4

from asyncpg import Connection
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio.session import _AsyncSessionContextManager
from sqlalchemy.orm import sessionmaker
from sqlalchemy.util import await_only

from ararat.db.connection import get_engine

_current_session_var: ContextVar["ArAsyncSession"] = ContextVar("_current_session")


class MissingCurrentSession(RuntimeError):
    pass


def get_current_session(allow_missing=False) -> Optional[AsyncSession]:
    if allow_missing:
        session = _current_session_var.get(None)
    else:
        try:
            session = _current_session_var.get()
        except LookupError:
            raise MissingCurrentSession(f"session not found in contextvar")

    current_task = asyncio.current_task()
    if session and session._asyncio_task is not current_task:
        if not allow_missing:
            raise MissingCurrentSession(
                f"found session ({session._asyncio_task=} does't match curret task ({current_task=})"
            )
        return None
    return session


C = TypeVar("C", bound=Callable)


class UniqIdConnection(Connection):
    def _get_unique_id(self, prefix: str) -> str:
        return f"__asyncpg_{prefix}_{uuid4()}__"


class SessionMaker(sessionmaker):
    def __init__(
        self, db_url: Optional[str] = None, hide_parameters: bool = True, connect_args: dict = None, **engine_kwargs
    ):
        self.engine: Optional[AsyncEngine] = None
        self.session_maker: Optional[sessionmaker] = None
        self.db_url: str = db_url
        self.hide_parameters = hide_parameters
        self.connect_args = connect_args
        self.engine_kwargs = engine_kwargs

    def initialize(self, db_url: Optional[str] = None, **engine_kwargs):
        if not db_url:
            db_url = self.db_url
        kwargs = {"connect_args": self.connect_args or {}, **self.engine_kwargs, **engine_kwargs}

        connect_args = kwargs["connect_args"]
        if "connection_class" not in connect_args:
            connect_args["connection_class"] = UniqIdConnection

        self.engine: AsyncEngine = get_engine(db_url, hide_parameters=self.hide_parameters, **kwargs)
        self.session_maker = sessionmaker(self.engine, class_=ArAsyncSession, expire_on_commit=False, autoflush=False)

    async def close(self):
        await self.engine.dispose()

    def begin(self):
        return self.session_maker.begin()

    def __call__(self, **local_kw):
        return self.session_maker.__call__(**local_kw)

    def configure(self, **new_kw):
        self.session_maker.configure(**new_kw)

    def __repr__(self):
        return self.session_maker.__repr__()

    def transactional(self):
        def dec(func: C) -> C:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                session = get_current_session(allow_missing=True)
                if session is None:
                    async with self.session_maker.begin():
                        return await func(*args, **kwargs)
                return await func(*args, **kwargs)

            return wrapper

        return dec

    def with_session(self):
        def dec(func: C) -> C:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                session = get_current_session(allow_missing=True)
                if session is None:
                    async with self.session_maker():
                        return await func(*args, **kwargs)
                return await func(*args, **kwargs)

            return wrapper

        return dec


class ArAsyncSession(AsyncSession):
    def run_after_commit(self, hook: Callable, *args, **kwargs):
        event.listens_for(self.sync_session, "after_commit")(lambda session: await_only(hook(*args, **kwargs)))

    async def __aenter__(self):
        self._current_session_var_token = _current_session_var.set(self)
        self._asyncio_task = asyncio.current_task()
        return await super().__aenter__()

    async def __aexit__(self, type_, value, traceback, reset_session_contextvar=True) -> None:
        await super().__aexit__(type_, value, traceback)
        if reset_session_contextvar:
            _current_session_var.reset(self._current_session_var_token)

    def _maker_context_manager(self):
        return ArAsyncSessionContextManager(self)


class ArAsyncSessionContextManager(_AsyncSessionContextManager):
    async def __aenter__(self):
        self.trans = self.async_session.begin()
        await self.trans.__aenter__()
        return await self.async_session.__aenter__()  # Вот здесь отличие от стандартной имплементации

    async def __aexit__(self, type_, value, traceback):
        async def go():
            await self.trans.__aexit__(type_, value, traceback)
            await self.async_session.__aexit__(type_, value, traceback, reset_session_contextvar=False)

        await asyncio.shield(go())
        # Вот здесь отличие от стандартной имплементации
        _current_session_var.reset(self.async_session._current_session_var_token)
