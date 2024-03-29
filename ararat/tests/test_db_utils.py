import asyncio
from datetime import datetime

import pytest
from sqlalchemy import Column, BigInteger, DateTime, Text, ForeignKey, cast, Integer, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import declarative_base, relationship, joinedload
from testcontainers.postgres import PostgresContainer

from ararat.common.dt import datetime_now
from ararat.db.dao import BaseDao
from ararat.db.session import SessionMaker, MissingCurrentSession

Base = declarative_base()


class TableForTest(Base):
    __tablename__ = "table_for_test"
    id: int = Column(BigInteger(), primary_key=True, autoincrement=True)
    creation_time: datetime = Column(DateTime(True), nullable=False)
    str_value: str = Column(Text())
    jsonb_value: dict = Column(JSONB())


class JoinedTableForTest(Base):
    __tablename__ = "table_for_test_joined"
    id: int = Column(BigInteger(), primary_key=True)
    table_for_test_id: int = Column(BigInteger(), ForeignKey("table_for_test.id"), nullable=False)
    table_for_test: TableForTest = relationship("TableForTest", lazy="raise")


Session = SessionMaker()


@pytest.fixture(scope="module")
async def session_maker(pg_container: PostgresContainer) -> SessionMaker:
    db_port = pg_container.get_exposed_port(pg_container.port_to_expose)
    db_url = (
        f"postgresql+asyncpg://{pg_container.get_container_host_ip()}:{db_port}/{pg_container.POSTGRES_DB}?"
        f"user={pg_container.POSTGRES_USER}&password={pg_container.POSTGRES_PASSWORD}"
    )

    global Session
    Session.initialize(db_url)
    yield Session
    await Session.close()


@pytest.fixture(scope="module", autouse=True)
async def init_db(session_maker: SessionMaker):
    async with session_maker.engine.begin() as con:
        await con.run_sync(Base.metadata.create_all)


@pytest.fixture(autouse=True)
async def delete_rows(session_maker: SessionMaker):
    async with session_maker.engine.begin() as con:
        await con.execute(text(f"DELETE FROM {JoinedTableForTest.__tablename__};"))
        await con.execute(text(f"DELETE FROM {TableForTest.__tablename__};"))


class TestAlchemy:
    async def test_error_without_active_session(self):
        with pytest.raises(MissingCurrentSession):
            await BaseDao().get(TableForTest, 1)

        async with Session():
            with pytest.raises(MissingCurrentSession):
                await asyncio.create_task(BaseDao().get(TableForTest, 1))

    async def test_common_operations(self):
        creation_time = datetime_now()
        async with Session.begin():
            obj1 = await BaseDao().add(
                TableForTest(creation_time=creation_time, str_value="example1", jsonb_value={"dt": creation_time})
            )
            obj2 = await BaseDao().add(
                TableForTest(creation_time=creation_time, str_value="example2", jsonb_value={"dt": creation_time})
            )
            obj_join = await BaseDao().add(JoinedTableForTest(id=1000, table_for_test_id=obj1.id))

        async with Session():
            empty_update = BaseDao().select(TableForTest).where(TableForTest.id == obj1.id + 1000)
            assert (await BaseDao().get_all(empty_update)) == []
            assert (await BaseDao().get_first(empty_update)) is None

            not_found_join_query = (
                BaseDao()
                .select(TableForTest, JoinedTableForTest)
                .join(JoinedTableForTest, onclause=TableForTest.id == JoinedTableForTest.table_for_test_id)
                .where(TableForTest.id == obj1.id + 1000)
            )
            assert (await BaseDao().get_all(not_found_join_query)) == []
            o1, o2 = await BaseDao().get_first(not_found_join_query)
            assert o1 is None
            assert o2 is None

            found_query = BaseDao().select(TableForTest).where(TableForTest.id == obj1.id)
            found_list = await BaseDao().get_all(found_query)
            assert len(found_list) == 1
            found_item: TableForTest = await BaseDao().get_first(found_query)
            assert found_item is not None
            assert found_item.id == obj1.id
            assert found_item.creation_time == pytest.approx(creation_time)

            found_join_query = (
                BaseDao()
                .select(TableForTest, JoinedTableForTest)
                .join(JoinedTableForTest, onclause=TableForTest.id == JoinedTableForTest.table_for_test_id)
                .where(TableForTest.id == obj1.id)
            )
            found_join_list = await BaseDao().get_all(found_join_query)
            assert len(found_join_list) == 1
            o1, o2 = found_join_list[0]
            assert o1.id == obj1.id
            assert o2.id == obj_join.id

        async with Session.begin():
            empty_update = (
                BaseDao()
                .update(TableForTest)
                .values({TableForTest.str_value: "new_value"})
                .where(TableForTest.id == obj1.id + 1000)
            )
            assert (await BaseDao().get_rows_count(empty_update)) == 0

            non_empty_update = BaseDao().update(TableForTest).values({TableForTest.str_value: "new_value"})
            assert (await BaseDao().get_rows_count(non_empty_update)) == 2

            non_empty_delete = BaseDao().delete(TableForTest).where(TableForTest.id == obj2.id)
            assert (await BaseDao().get_rows_count(non_empty_delete)) == 1

        assert (await self.delete_from_table(JoinedTableForTest)) == 1
        assert (await self.delete_from_table(JoinedTableForTest)) == 0

    async def test_join_option(self):
        creation_time = datetime_now()
        async with Session.begin():
            obj1 = await BaseDao().add(
                TableForTest(creation_time=creation_time, str_value="example1", jsonb_value={"dt": creation_time})
            )
            joined_obj_1 = await BaseDao().add(JoinedTableForTest(id=1000, table_for_test_id=obj1.id))
            joined_obj_2 = await BaseDao().add(JoinedTableForTest(id=1001, table_for_test_id=obj1.id))

        async with Session():
            found = await BaseDao().get_by_ids(JoinedTableForTest.id, [1000, 1001, 1002])
            assert len(found) == 2
        with pytest.raises(InvalidRequestError) as ex:
            found[0].table_for_test.id

        async with Session():
            found = await BaseDao().get_all(BaseDao().select(JoinedTableForTest))
            assert len(found) == 2
        with pytest.raises(InvalidRequestError) as ex:
            found[0].table_for_test.id

        async with Session():
            found = (
                await BaseDao()
                .options(joinedload(JoinedTableForTest.table_for_test))
                .get_by_ids(JoinedTableForTest.id, [1000, 1001, 1002])
            )
            assert len(found) == 2
        assert found[0].table_for_test.id == obj1.id
        assert found[1].table_for_test.id == obj1.id

        async with Session():
            dao = BaseDao()
            found = await dao.get_all(
                dao.options(joinedload(JoinedTableForTest.table_for_test)).select(JoinedTableForTest)
            )
            assert len(found) == 2
        assert found[0].table_for_test.id == obj1.id
        assert found[1].table_for_test.id == obj1.id

    async def test_base_dao_get_page(self):
        async with Session.begin():
            for i in range(1, 19):
                await BaseDao().add(TableForTest(creation_time=datetime_now(), str_value=str(i)))

        async with Session():
            page1 = await BaseDao().get_page(TableForTest.id, None, page_size=10, reverse=False)
            assert len(page1) == 10
            assert page1[-1].str_value == "10"

            page2 = await BaseDao().get_page(TableForTest.id, page1[-1].id, page_size=10, reverse=False)
            assert len(page2) == 8
            assert page2[-1].str_value == "18"

        async with Session():
            page1 = await BaseDao().get_page(TableForTest.id, None, page_size=10, reverse=True)
            assert len(page1) == 10
            assert page1[-1].str_value == "9"

            page2 = await BaseDao().get_page(TableForTest.id, page1[-1].id, page_size=10, reverse=True)
            assert len(page2) == 8
            assert page2[-1].str_value == "1"

        async with Session():
            page1 = (
                await BaseDao()
                .where(cast(TableForTest.str_value, Integer) % 2 == 0)
                .get_page(TableForTest.id, None, page_size=3, reverse=True)
            )
            assert len(page1) == 3
            assert page1[0].str_value == "18"
            assert page1[1].str_value == "16"
            assert page1[2].str_value == "14"

            page2 = (
                await BaseDao()
                .where(cast(TableForTest.str_value, Integer) % 2 == 0)
                .get_page(TableForTest.id, page1[-1].id, page_size=3, reverse=True)
            )
            assert len(page2) == 3
            assert page2[0].str_value == "12"
            assert page2[1].str_value == "10"
            assert page2[2].str_value == "8"

    async def test_select_one_field(self):
        values = []
        async with Session.begin():
            for i in range(1, 19):
                values.append(await BaseDao().add(TableForTest(creation_time=datetime_now(), str_value=str(i))))

        async with Session():
            dao = BaseDao()
            result = await dao.get_all(
                dao.select(TableForTest.id)
                .where(cast(TableForTest.str_value, Integer) > 10)
                .order_by(TableForTest.id.asc())
            )
            assert len(result) == 8
            assert result[0] == values[10].id
            assert result[7] == values[17].id

    @Session.transactional()
    async def delete_from_table(self, table) -> int:
        dao = BaseDao()
        return await dao.get_rows_count(dao.delete(table))
