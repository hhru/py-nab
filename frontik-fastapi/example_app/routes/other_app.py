from fastapi import APIRouter, Query, HTTPException
from starlette.responses import JSONResponse

from ffapi.router import FrontikFastAPIRoute

app_router = APIRouter(prefix="/other_app", route_class=FrontikFastAPIRoute, dependencies=[])


@app_router.get("/route")
async def route(error: bool = Query(False)):
    if error:
        raise HTTPException(502)
    return JSONResponse({"route_1": "dict"})
