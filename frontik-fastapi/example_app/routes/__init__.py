import asyncio
import logging
import typing
from typing import TypeVar, List

from fastapi import APIRouter, Query, Depends
from frontik.handler import PageHandler
from pydantic import BaseModel

from ffapi.dep import async_dep, DepBuilder
from ffapi.handler import get_current_handler
from ffapi.router import FrontikFastAPIRoute

app_router = APIRouter(prefix="/fastapi", route_class=FrontikFastAPIRoute, dependencies=[])

logger = logging.getLogger(__name__)


class StatusResponse(BaseModel):
    query: int


T = TypeVar("T")


async def fetch_resume_ids(handler: PageHandler = Depends(get_current_handler)) -> List[int]:
    await handler.get_url("127.0.0.1:8080", "/other_app/route?fetch=resume_ids")
    return [1, 2, 3]


async def fetch_current_user_status(handler: PageHandler = Depends(get_current_handler)) -> List[int]:
    await handler.get_url("127.0.0.1:8080", "/other_app/route?fetch=current_user_status")
    return [1, 2, 3]


async def fetch_user_ids(
    handler: PageHandler = Depends(get_current_handler), resume_ids=async_dep(fetch_resume_ids)
) -> List[int]:
    resume_ids = await resume_ids
    await handler.get_url("127.0.0.1:8080", "/other_app/route?fetch=user_ids")
    return [4, 5, 6]


async def fetch_users(
    handler: PageHandler = Depends(get_current_handler), user_ids=async_dep(fetch_user_ids)
) -> typing.Mapping[int, dict]:
    user_ids = await user_ids
    await handler.get_url("127.0.0.1:8080", "/other_app/route?fetch=users_by_ids")
    return {1: {"id": 1}}


async def fetch_vacancy(
    handler: PageHandler = Depends(get_current_handler), users=async_dep(fetch_users)
) -> typing.Mapping[int, dict]:
    users = await users
    await handler.get_url("127.0.0.1:8080", "/other_app/route?fetch=vacancy")
    return {1: {"id": 1}}


async def fetch_activity_time_by_user_id(
    handler: PageHandler = Depends(get_current_handler), user_ids=async_dep(fetch_user_ids)
) -> typing.Mapping[int, int]:
    user_ids = await user_ids
    await handler.get_url("127.0.0.1:8080", "/other_app/route?fetch=fetch_activity_time")
    return {1: 1}


async def fetch_resume_status(
    handler: PageHandler = Depends(get_current_handler), resume_ids=async_dep(fetch_resume_ids)
) -> List[str]:
    resume_ids = await resume_ids

    await handler.get_url("127.0.0.1:8080", "/other_app/route?fetch=resume_status")
    return ["blocked"]


async def fetch_topics(
    handler: PageHandler = Depends(get_current_handler),
    resume_ids=async_dep(fetch_resume_ids),
    vacancy=async_dep(fetch_vacancy),
) -> List[str]:
    resume_ids, vacancy = await asyncio.gather(resume_ids, vacancy)

    await handler.get_url("127.0.0.1:8080", "/other_app/route?fetch=topics")
    return ["blocked"]


@app_router.get("/route", response_model=StatusResponse)
async def example_route(
    # query_param: int = Query(),
    current_status=async_dep(fetch_current_user_status),
    vacancy=async_dep(fetch_vacancy),
    activity=async_dep(fetch_activity_time_by_user_id),
    users=async_dep(fetch_users),
    resume_status=async_dep(fetch_resume_status),
    topics=async_dep(fetch_topics),
) -> StatusResponse:
    vacancy, activity, users, resume_status, topics, current_status = await asyncio.gather(
        vacancy, activity, users, resume_status, topics, current_status
    )
    return StatusResponse(query=123)


@app_router.get("/route_dynamic_style", response_model=StatusResponse)
async def route_fastapi_style() -> StatusResponse:
    await (await DepBuilder(example_route).build())
    return StatusResponse(query=123)
