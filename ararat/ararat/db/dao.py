from collections import defaultdict
from typing import Optional, Union, Collection, TypeVar, Type, Any, Tuple, List, Dict

from sqlalchemy import update, delete, select
from sqlalchemy.engine import CursorResult, Result
from sqlalchemy.sql import Executable, Select, Update, Delete

from ararat.db.session import get_current_session, ArAsyncSession

T = TypeVar("T")
C1 = TypeVar("C1")
C2 = TypeVar("C2")


class BaseDao:
    def __init__(self, session: Optional[ArAsyncSession] = None) -> None:
        if session is None:
            session = get_current_session()
        self._session = session
        self._options = None
        self._criteria = None
        self._order_by = None

    def options(self: T, *options) -> T:
        if not self._options:
            self._options = list(options)
        else:
            self._options.extend(options)
        return self

    def where(self: T, *criteria) -> T:
        if not self._criteria:
            self._criteria = list(criteria)
        else:
            self._criteria.extend(criteria)
        return self

    def order_by(self: T, *order_by):
        if not self._order_by:
            self._order_by = list(order_by)
        else:
            self._order_by.extend(order_by)
        return self

    async def execute(self, stmt: Executable, *args, **kwargs) -> Union[CursorResult, Result]:
        return await self._session.execute(stmt, *args, **kwargs)

    def select(self, *args) -> Select:
        if self._options:
            return select(*args).options(*self._options)
        return select(*args)

    def update(self, *args) -> Update:
        if self._options:
            return update(*args).options(*self._options)
        return update(*args)

    def delete(self, *args) -> Delete:
        if self._options:
            return delete(*args).options(*self._options)
        return delete(*args)

    async def get(self, entity: Type[T], ident: Any, *args, **kwargs) -> Optional[T]:
        return await self._session.get(entity, ident, *args, **kwargs)

    async def get_by_ids(self, column: C1, ids: Collection[C1], preserve_order=False) -> List[T]:
        if not ids:
            return []
        stmt = self.select(column.parent).filter(column.in_(ids))
        if self._criteria:
            stmt = stmt.where(*self._criteria)
        if self._order_by:
            stmt = stmt.order_by(*self._order_by)
        result = await self.get_all(stmt)
        if not preserve_order or len(result) <= 1:
            return result

        mapping = {getattr(item, column.key): item for item in result}
        return [item for id_ in ids if (item := mapping.get(id_)) is not None]

    async def get_map_by_ids(
        self, *, column: C1, ids: Collection[C1], map_column: C2 = None, reduce=True
    ) -> Dict[Union[C2, C1], T]:
        if not ids:
            return {}
        result = await self.get_by_ids(column, ids)
        if map_column is None:
            map_column = column
        if reduce:
            return {getattr(item, map_column.key): item for item in result}

        result_dict = defaultdict(list)
        for item in result:
            result_dict[getattr(item, map_column.key)].append(item)
        return result_dict

    async def add(self, obj: T) -> T:
        self._session.add(obj)
        await self._session.flush()
        return obj

    async def add_all(self, items: List[T]) -> List[T]:
        self._session.add_all(items)
        await self._session.flush()
        return items

    async def get_first(self, stmt) -> Union[Any, Tuple[Any, ...]]:
        result = await self.execute(stmt)
        result = self._configure_result(result, stmt)

        query_result = result.first()
        if query_result is not None:
            return query_result

        results_count = len(stmt.column_descriptions)
        if results_count == 1:
            return None

        return (None,) * results_count

    async def get_all(self, stmt) -> Union[List[Any], List[Tuple[Any, ...]]]:
        result = await self.execute(stmt)
        result = self._configure_result(result, stmt)
        return result.all()

    async def get_rows_count(self, stmt) -> int:
        result = await self.execute(stmt)
        return result.rowcount

    def _configure_result(self, result, stmt):
        if result.raw.context.compiled.compile_state.multi_row_eager_loaders:
            result = result.unique()
        if len(stmt.column_descriptions) == 1:
            result = result.scalars()
        return result

    async def __aenter__(self):
        return self

    async def __aexit__(self, type_, value, traceback):
        return

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        return
