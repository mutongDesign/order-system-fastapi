import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

project_root = Path(__file__).parent
sys.path.append(str(project_root))
from fastapi import FastAPI, Depends, HTTPException, Request, Response

from administrator import login, AdministratorRouters
from designer import DesignerRouters
from designer.DesignerLogin import websocket_designer_login
from root.RootWebsocket import watch_login_status
from order import OrderRouters
from financeCenter import FinanceCenterRouters
from works import WorksRouters
import jwt
from .core.security import jwt_token_key,oauth2_scheme
import logging
logger = logging.getLogger("uvicorn")

async def verify_permission(response:Response,request:Request):
    if request.url.path in ("/login",
                            "/administrator_register",
                            "/designer/register",
                            ):
        return
    try:
        token =await oauth2_scheme(request)
        logger.info(f"88888888888888verify_permission token={token}")

        if token:
            try:
                jwt_verify_data = jwt.decode(token, key=jwt_token_key, algorithms=["HS256"])
            except jwt.InvalidTokenError as e:
                raise HTTPException(status_code=401, )

        else:
            print(222222222)
            raise HTTPException(status_code=401, )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")



tz_sh = ZoneInfo("Asia/Shanghai")

scheduler=AsyncIOScheduler(timezone=tz_sh)

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    scheduler.add_job(
        OrderRouters.clear_timeout_orders_async,
        'interval',
        hours=2,
        id='clear_timeout_orders',
        replace_existing=True,
        misfire_grace_time=300,
        next_run_time=datetime.now(tz_sh)
    )
    if not scheduler.running:
        scheduler.start()

    yield
    if scheduler.running:
        scheduler.shutdown(wait=True)

app = FastAPI(dependencies=[Depends(verify_permission)], lifespan=app_lifespan)
app.include_router(login.router)
app.include_router(AdministratorRouters.router)
app.include_router(OrderRouters.Router)
app.include_router(DesignerRouters.Router)
app.include_router(FinanceCenterRouters.ROUTER)
app.include_router(WorksRouters.ROUTER)
app.add_websocket_route("/designerLogin", websocket_designer_login)
app.add_websocket_route("/watch_login_status", watch_login_status)



