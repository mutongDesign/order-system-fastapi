import random
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from sqlalchemy.ext.asyncio import AsyncSession

from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO , format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


logger = logging.getLogger("uvicorn")
order_cleaner = logging.getLogger("order_cleaner")
order_cleaner.setLevel(logging.INFO)

from faker import Faker

fake = Faker('zh_CN')

from sqlalchemy import func, insert, or_, select, update
from sqlalchemy.orm import Session, contains_eager, selectinload

from administrator.AdministratorTableBase import AdministratorTableBase

from .OrderTableBase import OrderTableBase, OrderNotificationTableBase
from order.OrderModels import OrderCreateModel, OrderSearchResponseModel, OrderUpDateModel, OrderNotificationModel

from core.CreateEngine import engine, async_engine
from fastapi import FastAPI, HTTPException, APIRouter, Body, Query, Path, status

from financeCenter.FinanceCenterTableBase import DesignerWithdrawApplicationTable, DesignerAccountTableBase
from designer.DesignerTableBase import  DesignerRegisterTable

from root.RootWebsocket import manager

Router = APIRouter()

# 订单查询
@Router.post("/order/query")
def order_query(page: int = Query(1, ge=1), role: str = Query(), role_id: str = Query(), query_info=Body()):
    with Session(engine) as session, session.begin():
        all_orders_count = session.query(func.count(OrderTableBase.id)).scalar()
        if role == "designer":
            query = session.query(OrderTableBase).outerjoin(OrderTableBase.administratorTableBase).outerjoin(
                OrderTableBase.designerRegisterTable).options(contains_eager(OrderTableBase.administratorTableBase),
                                                              contains_eager(
                                                                  OrderTableBase.designerRegisterTable)).filter(
                OrderTableBase.designer_id == role_id)
        else:
            query = session.query(OrderTableBase).outerjoin(OrderTableBase.administratorTableBase).outerjoin(
                OrderTableBase.designerRegisterTable).options(contains_eager(OrderTableBase.administratorTableBase),
                                                              contains_eager(OrderTableBase.designerRegisterTable))

        query_condition_list = []
        search_condition_list = []

        if query_info['orderType'] != '全部':
            query_condition_list.append(OrderTableBase.order_type == query_info['orderType'])

        if query_info["orderStatus"] != "全部":
            query_condition_list.append(OrderTableBase.order_status == query_info['orderStatus'])
        if query_info["startTime"]:
            query_condition_list.append(OrderTableBase.created_at >= query_info['startTime'])

        if query_info["endTime"]:
            query_condition_list.append(OrderTableBase.created_at <= query_info['endTime'])

        if query_info["administratorUserName"] != "":
            query_condition_list.append(AdministratorTableBase.user_name == query_info['administratorUserName'])

        query_orders_query = query.filter(*query_condition_list).order_by(OrderTableBase.created_at.desc())

        if query_info["searchContent"] != "":
            search_and_query_orders_query = query_orders_query.filter(
                or_(
                    OrderTableBase.order_id.like(f"%{query_info['searchContent']}%"),
                    OrderTableBase.order_title.like(f"%{query_info['searchContent']}%"),
                )
            )
        else:
            search_and_query_orders_query = query_orders_query

        response_search_and_query_orders_count = search_and_query_orders_query.with_entities(
            func.count(OrderTableBase.id).distinct()).scalar()

        search_and_query_orders_data = search_and_query_orders_query.offset((int(page) - 1) * 10).limit(10).all()
        response_search_and_query_orders_data = [OrderSearchResponseModel.model_validate(order) for order in
                                                 search_and_query_orders_data]
        total_pages = max(1, (response_search_and_query_orders_count + 10 - 1) // 10)

    return {
        'totalPages': total_pages,
        'allOrdersCount': all_orders_count,
        'responseSearchOrdersCount': response_search_and_query_orders_count,
        'responseSearchOrdersData': response_search_and_query_orders_data,
    }


# 订单插入
@Router.post("/order/insert")
def order_insert(insert_data_number=Body(embed=True)):
    order_data = []
    try:
        for i in range(insert_data_number):
            order_data.append({
                "order_id": f"{datetime.now().strftime('%y%m%d%H%M%S')}{random.randint(100, 999)}",
                "order_type": random.choice(
                    ['UI设计', 'UX设计', '网站设计', '品牌设计', '移动应用设计', 'Logo设计', '插画设计', '包装设计',
                     '其他设计']),
                "order_title": f"{fake.company_prefix()} 订单-{random.choice(['UI设计', 'UX设计', '网站设计', '品牌设计', '移动应用设计', 'Logo设计', '插画设计', '包装设计', '其他设计'])}-{i + 1}",
                "supervisor_id": "8620251115",
                "order_status": random.choice(["待分配", "进行中", "已完成", "已退款", "已取消"]),
                "order_overview": f"{fake.sentence(nb_words=20)}",
                "created_at": fake.date_time_between(start_date="now", end_date="+30d"),
                "delivery_deadline": fake.date_time_between(start_date="+31d", end_date="+300d"),
                "amount": random.randint(100, 10000)
            })

        with Session(engine) as session, session.begin():
            session.execute(
                insert(OrderTableBase), order_data
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据错误{str(e)}")


# 订单删除
@Router.delete("/orders/delete")
def order_delete(delete_data_order_id=Body(embed=True)):
    with Session(engine) as session, session.begin():
        session.query(OrderTableBase).filter(OrderTableBase.order_id == delete_data_order_id).delete()


# 订单创建
@Router.post(path="/create_order")
async def create_order(response_model: OrderCreateModel = Body(...)):
    try:

        with Session(bind=engine) as session, session.begin():
            create_order_info = OrderTableBase(
                order_id=response_model.order_id,
                order_type=response_model.order_type,
                order_title=response_model.order_title,
                supervisor_id=response_model.supervisor_id,
                order_status=response_model.order_status,
                order_overview=response_model.order_overview,
                delivery_deadline=response_model.order_deadline,
                amount=response_model.order_amount,
            )

            session.add(create_order_info)
        return {"message": "User created", "data": response_model.model_dump()}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


# 订单修改
@Router.patch(path="/update_order")
async def update_order(request_data: OrderUpDateModel = Body(...)):
    try:
        update_dict = request_data.model_dump(exclude_unset=True)
        with Session(bind=engine) as session, session.begin():
            update_query = session.query(OrderTableBase).filter(OrderTableBase.order_id == request_data.order_id)
            update_query.update(update_dict['change_item'])
        return {"message": "User update"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


# 订单状态修改
@Router.patch(path="/orders/{order_id}/change-order-status")
async def change_order_status(order_id:str = Path(...), request_data:OrderUpDateModel= Body(...)):
    try:
        with Session(bind=engine) as session, session.begin():
            session.execute(update(OrderTableBase).where(OrderTableBase.order_id == order_id).values(order_status=request_data.order_status))
        return {"message": "order-update-ok"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


# 订单查收状态修改
@Router.patch(path="/orders/{order_id}/designer-change-order-receive-status")
async def designer_change_order_receive_status(order_id:str = Path(...), request_data:OrderUpDateModel= Body(...)):
    try:
        with Session(bind=engine) as session, session.begin():
            matched_order = session.execute(select(OrderTableBase).filter(OrderTableBase.order_id == order_id)).scalar_one_or_none()
            if matched_order.designer_id == request_data.designer_id and matched_order.order_status == "待查收":
                matched_order.order_status= request_data.order_status
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")



# 批量订单修改
@Router.patch(path="/change-all-order-status")
async def change_all_order_status():
    try:
        with Session(bind=engine) as session, session.begin():
            order = session.execute(update(OrderTableBase).values(order_status="待分配",accounting_status=False))
        return {"message": "User update"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")



# 订单设计师指派
@Router.put(path="/orders/{order_id}/assign-designer")
async def assign_designer(order_id: str = Path(...), assign_designer_id: str = Body(...)):
    try:
        with Session(bind=engine) as session, session.begin():
            matched_order = session.execute(
                select(OrderTableBase).filter(OrderTableBase.order_id == order_id)).scalar_one_or_none()
            matched_designer = session.execute(select(DesignerRegisterTable).filter(
                DesignerRegisterTable.user_id == assign_designer_id)).scalar_one_or_none()
            session.add(OrderNotificationTableBase(
                order_id=order_id,
                designer_id=assign_designer_id,
                notification="",
                delivery_status=0,
            ))
            if not matched_designer:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f"设计师ID {assign_designer_id} 不存在，请检查ID是否正确")
            logger.info(matched_order.designer_id)
            matched_order.designer_id = assign_designer_id
            matched_order.order_status="待查收"
            matched_order.assign_at=datetime.now()

            await manager.new_order_broadcast(
                assign_designer_id,
                {
                    "type": "now_order_notification",
                })

        return {"message": "designer update"}
    except Exception as e:
        logger.info(str(e))



# 超时订单清理

tz_sh = ZoneInfo("Asia/Shanghai")
async def clear_timeout_orders_async():
    timeout_threshold = datetime.now(tz_sh) - timedelta(hours=2)
    logger.info("========== 开始执行超时订单清理任务 ==========")
    order_cleaner.info(f"超时阈值时间：{timeout_threshold}")
    async with AsyncSession(bind=async_engine) as session:
        async with session.begin():
            result = await session.execute(update(OrderTableBase).where(
                OrderTableBase.order_status=="待查收",
                OrderTableBase.designer_id.isnot(None),
                OrderTableBase.assign_at < timeout_threshold,
            ).values(
                order_status="查收超时"
            ))


@Router.get("/test_clear_orders")
async def test_clear_orders():
    await clear_timeout_orders_async()
    return {"msg": "任务执行完成，查看日志"}


# 查询订单通知
@Router.post(path="/orders/{user_id}/search-order-notification")
def search_order_notification(user_id: str = Path(...)):
    try:
        with Session(bind=engine) as session, session.begin():
            logger.info(user_id)

            matched_order_notification=session.execute(select(OrderNotificationTableBase).filter(
                OrderNotificationTableBase.is_read == False,
                OrderNotificationTableBase.designer_id == user_id,
            )).scalars().all()

            session.execute(update(OrderNotificationTableBase).where(
                OrderNotificationTableBase.order_id == user_id,
                OrderNotificationTableBase.designer_id == user_id,
            ).values(delivery_status=1))

            # matched_order_notification_count = session.execute(select(func.count(OrderNotificationTableBase.id)).filter(
            #     OrderNotificationTableBase.is_read == False,
            #     OrderNotificationTableBase.designer_id == user_id,
            # )
            # ).scalar_one_or_none()

            logger.info(f'88888888888{matched_order_notification}')
            return {
                "unread_notification": [OrderNotificationModel.model_validate(value) for value in matched_order_notification],
            }

    except Exception as e:
        logger.info(str(e))

# 更改订单通知读取状态并返回订单信息
@Router.get(path="/orders/{order_id}/get-order-details")
async def get_order_details(order_id: str = Path(...)):
    logger.info(f"666666666666:{order_id}")
    with Session(bind=engine) as session, session.begin():
        order_notification = session.execute(select(OrderNotificationTableBase).filter(OrderNotificationTableBase.order_id == order_id, OrderNotificationTableBase.is_read==False)).scalar()
        order = session.execute(select(OrderTableBase).filter(OrderTableBase.order_id == order_id)).scalar_one_or_none()
        logger.info(f"order_id:{order}")
        if order_notification:
            order_notification.is_read = True

        return {
            "is_update_success": True,
            "order_data": OrderSearchResponseModel.model_validate(order),
        }

# 订单完成入账状态修改
@Router.post(path="/update_completed_accounting_status")
async def update_accounting_status(request_data: OrderUpDateModel = Body(...)):
    try:
        async with AsyncSession(bind=async_engine) as session:

            async with session.begin():
                # 1. 查询订单并加行锁（修正：with_for_update() 缺少括号），预加载设计师关联对象
                result = await session.execute(
                    select(OrderTableBase)
                    .options(selectinload(OrderTableBase.designerRegisterTable).selectinload(DesignerRegisterTable.administratorTableBase),selectinload(OrderTableBase.administratorTableBase))  # 预加载，避免延迟加载
                    .filter(OrderTableBase.order_id == request_data.order_id)
                    .with_for_update()  # 修正：补充括号，加行锁
                )
                matched_order = result.scalar_one_or_none()

                if not matched_order:
                    raise HTTPException(status_code=404, detail="订单不存在")

                if not matched_order.designer_id:
                    raise HTTPException(status_code=404, detail="订单未指派设计师")

                matched_order.accounting_status = True

                designer = matched_order.designerRegisterTable
                if matched_order.order_status == "进行中":
                    matched_order.order_status = "已完成"
                    designer.withdrawable_amount += matched_order.amount
                    designer.total_income += matched_order.amount

                add_designer_account_dict = {
                    "balance_after" : designer.withdrawable_amount,
                    "designer_id" : designer.user_id,
                    "order_id" : matched_order.order_id,
                    "transaction_type" : '订单收入',
                    "change_amount" : matched_order.amount,
                }

                await session.execute(insert(DesignerAccountTableBase).values(add_designer_account_dict))
                logger.info(f"order_id:{matched_order.designerRegisterTable.user_id}")
                return {"message": "set completed accounting status is ok"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
