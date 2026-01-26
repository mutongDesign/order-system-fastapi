import random
from calendar import monthrange
from datetime import datetime, timedelta

import logging
from msilib.schema import Patch
from zoneinfo import ZoneInfo

from sqlalchemy.util import ordered_column_set

from dateutil.relativedelta import relativedelta

logger = logging.getLogger("uvicorn")

from faker import Faker
fake = Faker('zh_CN')

from fastapi import APIRouter, Body, HTTPException, Query, Form, UploadFile, File,Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, insert, select, distinct
from sqlalchemy.orm import Session, selectinload
from .DesignerModels import DesignerRegisterModel
from core.CreateEngine import engine
from .DesignerTableBase import DesignerRegisterTable

from core.security import pwd_passlib
from core.CreateEngine import async_engine
from .DesignerModels import DesignerSearchResponseModel

from administrator.AdministratorTableBase import AdministratorTableBase



from order.OrderTableBase import OrderTableBase
from order.OrderModels import OrderSearchResponseModel

Router = APIRouter()

from core.CloudAuth import upload_user_avatar_to_qiniu, upload_image_to_qcloud, delete_image_to_qcloud, upload_image_to_upyun,delete_image_to_upyun

@Router.post('/designer/register')
def designer_register(designer_register_data:DesignerRegisterModel=Body(...)):
    passlib_user_password = pwd_passlib.hash(designer_register_data.userPassword)
    get_designer_register_data=DesignerRegisterTable(
        name=designer_register_data.name,
        age=designer_register_data.age,
        gender=designer_register_data.gender,
        cell_phone_number=designer_register_data.cellPhoneNumber,
        email=designer_register_data.email,
        user_name=designer_register_data.userName,
        user_password=passlib_user_password,
        professional_field=designer_register_data.professionalField,
        user_id=designer_register_data.userId,
    )
    try:
        with Session(engine) as session, session.begin():
            session.add(get_designer_register_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"请检查数据类型{str(e)}")

@Router.post('/designer/search')
def design_search(page:int=Query(1,ge=1),req_data=Body(...)):
    try:
        with Session(engine) as session, session.begin():
            logger.info(req_data['professionalField'])
            count=session.query(func.count(DesignerRegisterTable.id)).scalar()
            query= session.query(DesignerRegisterTable).outerjoin(DesignerRegisterTable.administratorTableBase) .options(selectinload(DesignerRegisterTable.administratorTableBase))
            print(query.all())
            query_list=[]
            if req_data["professionalField"]!='全部领域':
                query_list.append(DesignerRegisterTable.professional_field == req_data["professionalField"])

            search_design_query = query.filter(*query_list)
            print(search_design_query.all(),333333333)
            response_search_design_count = search_design_query.with_entities(func.count(DesignerRegisterTable.id).distinct()).scalar()
            print(response_search_design_count,5555555555555555)

            search_design_query_data = search_design_query.offset((int(page) - 1) * 10).limit(10).all()
            print(search_design_query_data, 77777777777777777)
            response_search_design_query_data = [DesignerSearchResponseModel.model_validate(designer) for designer in search_design_query_data]
            print(response_search_design_query_data, 8888888888888888888888888)

            total_pages = max(1, (response_search_design_count + 10 - 1) // 10)
            print(total_pages,666666666666666666666666)
            print(count)
            print(response_search_design_count)
            print(response_search_design_query_data)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        'totalPages': total_pages,
        'allOrdersCount': count,
        'responseSearchDesignerCount': response_search_design_count,
        'responseSearchDesignerData': response_search_design_query_data,
    }


@Router.post("/designer/insert" )
def order_insert(insert_data_number=Body(embed=True)):
    designer_data = []
    try:
        for i in range(insert_data_number):
            designer_data.append({
                "order_id": f"ORD{datetime.now().strftime('%Y%m%d')}{random.randint(100, 999)}",
                "name": fake.name(),
                "age": fake.random_int(min=18, max=60),
                "cell_phone_number": fake.phone_number(),
                "email": fake.email(),
                "user_name": fake.user_name(),
                "professional_field": random.choice(["电商视觉", "平面广告"]),

                "supervisor_id": "8620251115",  # 关联管理员
                "order_overview": f"{fake.sentence(nb_words=20)}",
                "created_at": fake.date_time_between(start_date="now", end_date="+30d"),
                "delivery_deadline": fake.date_time_between(start_date="+31d", end_date="+300d"),
                "amount": random.randint(100, 10000)
            })


        with Session(engine) as session, session.begin():
            session.execute(
                insert(DesignerRegisterTable), designer_data
            )
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"数据错误{str(e)}")

@Router.post("/designer/self/search")
def designer_self_search(request_data=Body(...)):
    logger.info(f"测试数据{request_data['userId']}")
    try:
        with Session(engine) as session, session.begin():
            query_table = session.query(DesignerRegisterTable).filter(DesignerRegisterTable.user_id == request_data['userId']).first()
            return {
                "user_data":DesignerSearchResponseModel.model_validate(query_table)
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 查询数据仪表盘所用数据
@Router.get("/dashboard-data/{admin_id}")
async def get_dashboard_data(admin_id:str=Path(...)):
    try:
        async with AsyncSession(async_engine) as session:
            async with session.begin():
                # 设计师总数量
                designer_count_result = await session.execute(
                    select(func.count(DesignerRegisterTable.id))
                )
                designer_count=designer_count_result.scalar()

                #在线的设计师数量
                online_designer_count_result = await session.execute(
                    select(func.count(DesignerRegisterTable.id))
                    .where(DesignerRegisterTable.on_line_status == True)
                )
                online_designer_count=online_designer_count_result.scalar()

                # 今日新增订单量
                today=datetime.today()
                start_time_of_today =datetime.combine(today, datetime.min.time())
                end_time_of_today =datetime.combine(today, datetime.max.time())
                today_order_count_result = await session.execute(
                    select(func.count(OrderTableBase.id))
                    .where(
                        OrderTableBase.created_at >= start_time_of_today,
                        OrderTableBase.created_at <= end_time_of_today,
                           )
                )
                today_order_count=today_order_count_result.scalar()

                 # 今日新增订单金额
                today_order_total_amount_result = await session.execute(
                    select(func.sum(OrderTableBase.amount))
                    .where(
                        OrderTableBase.created_at >= start_time_of_today,
                        OrderTableBase.created_at <= end_time_of_today,
                           )
                )
                today_order_total_amount=today_order_total_amount_result.scalar()

                # 今日定稿订单量
                today_finalized_order_total_count_result = await session.execute(
                    select(func.count(OrderTableBase.id))
                    .where(
                        OrderTableBase.approved_at >= start_time_of_today,
                        OrderTableBase.approved_at <= end_time_of_today,
                           )
                )
                today_finalized_order_total_count=today_finalized_order_total_count_result.scalar()

                 # 今日定稿订单总金额
                today_finalized_order_total_amount_result = await session.execute(
                    select(func.sum(OrderTableBase.amount))
                    .where(
                        OrderTableBase.approved_at >= start_time_of_today,
                        OrderTableBase.approved_at <= end_time_of_today,
                           )
                )
                today_finalized_order_total_amount=today_finalized_order_total_amount_result.scalar()


                # 当月订单量
                now = datetime.now(ZoneInfo('Asia/Shanghai'))
                year, month = now.year, now.month
                first_day_in_month = datetime(year,month,1)
                _, last_day_num=monthrange(year,month)

                last_day_in_month = datetime(year, month, last_day_num, 23, 59, 59, 999999,tzinfo=ZoneInfo('Asia/Shanghai'))

                matched_new_order_in_month_result = await session.execute(
                    select(func.count(OrderTableBase.id))
                    .where(
                        OrderTableBase.created_at >= first_day_in_month,
                        OrderTableBase.created_at <= last_day_in_month,
                    )
                )
                matched_new_order_in_month=matched_new_order_in_month_result.scalar()


                order_count_of_mouth_object = {}
                order_amount_of_mouth_object = {}
                finalized_order_count_of_mouth_object = {}
                finalized_order_amount_of_mouth_object = {}
                order_of_mouth_object = {}
                mouth_list = []


                for num in range(12):

                    target_date =now -  relativedelta(months=num)
                    year, month = target_date.year, target_date.month

                    first_day_in_month = datetime(year, month, 1)
                    _, last_day_num = monthrange(year, month)
                    last_day_in_month = datetime(year, month, last_day_num, 23, 59, 59, 999999)

                    # 用"年-月"作为键，比如"2026-01"
                    key = f"{year}-{month:02d}"

                    # 计算当月订单量
                    order_count_of_mouth_result = await session.execute(
                        select(func.count(OrderTableBase.id))
                        .where(
                            OrderTableBase.created_at >= first_day_in_month,
                            OrderTableBase.created_at <= last_day_in_month,
                        )
                    )
                    order_count_of_mouth = order_count_of_mouth_result.scalar()
                    order_count_of_mouth_object[key] = order_count_of_mouth

                    # 计算当月订单额
                    order_amount_of_mouth_result = await session.execute(
                        select(func.sum(OrderTableBase.amount))
                        .where(
                            OrderTableBase.created_at >= first_day_in_month,
                            OrderTableBase.created_at <= last_day_in_month,
                        )
                    )
                    order_amount_of_mouth = order_amount_of_mouth_result.scalar() or 0.0
                    order_amount_of_mouth_object[key]=order_amount_of_mouth

                    # 计算当月定稿订单量
                    finalized_order_count_of_mouth_result = await session.execute(
                        select(func.count(OrderTableBase.id))
                        .where(
                            OrderTableBase.approved_at >= first_day_in_month,
                            OrderTableBase.approved_at <= last_day_in_month,
                        )
                    )
                    finalized_order_count_of_mouth = finalized_order_count_of_mouth_result.scalar()
                    finalized_order_count_of_mouth_object[key] = finalized_order_count_of_mouth

                    # 计算当月定稿订单额
                    finalized_order_amount_of_mouth_result = await session.execute(
                        select(func.sum(OrderTableBase.amount))
                        .where(
                            OrderTableBase.assign_at >= first_day_in_month,
                            OrderTableBase.assign_at <= last_day_in_month,
                        )
                    )
                    finalized_order_amount_of_mouth = finalized_order_amount_of_mouth_result.scalar() or 0.0
                    finalized_order_amount_of_mouth_object[key]=finalized_order_amount_of_mouth
                    if key not in order_of_mouth_object:
                        order_of_mouth_object[key] = {}

                    order_of_mouth_object[key]["订单量"] = order_count_of_mouth
                    order_of_mouth_object[key]["订单额"] = order_amount_of_mouth
                    order_of_mouth_object[key]["定稿订单量"] = finalized_order_count_of_mouth
                    order_of_mouth_object[key]["定稿订单额"] = finalized_order_amount_of_mouth

                    mouth_list.append(key)


                # 订单总量
                ordered_total_count_result = await session.execute(select(func.count(OrderTableBase.id)))
                ordered_total_count = ordered_total_count_result.scalar()

                # 待分配的订单量
                pending_orders_count_result = await session.execute(select(func.count(OrderTableBase.id)).filter( OrderTableBase.order_status == "待分配"))
                pending_orders_count = pending_orders_count_result.scalar()

                # 进行中的订单
                ongoing_orders_count_result = await session.execute(
                    select(func.count(OrderTableBase.id)).filter(OrderTableBase.order_status == "进行中"))
                ongoing_orders_count = ongoing_orders_count_result.scalar()


                # 超时订单数
                unconfirmed_assignment_count_result = await session.execute(
                    select(func.count(OrderTableBase.id)).where(OrderTableBase.order_status == "查收超时"))
                unconfirmed_assignment_count = unconfirmed_assignment_count_result.scalar()

                # 查询订单类型及订单各类型的数量
                order_type_object={}
                order_type_total_amount_object={}
                matched_orders_type_result = await session.execute(
                    select(distinct(OrderTableBase.order_type)).filter(OrderTableBase.order_type.isnot(None)))
                matched_orders_type = matched_orders_type_result.scalars().all()
                for order in matched_orders_type:
                    # 各类型订单数量
                    matched_orders_type_count_result = await session.execute(
                        select(func.count(OrderTableBase.id)).filter(OrderTableBase.order_type == order))
                    matched_orders_type_count = matched_orders_type_count_result.scalar()
                    order_type_object[order]=matched_orders_type_count

                     # 各类型订单数量
                    orders_type_total_amount_result = await session.execute(
                        select(func.sum(OrderTableBase.amount)).where(OrderTableBase.order_type == order))
                    orders_type_total_amount = orders_type_total_amount_result.scalar()
                    order_type_total_amount_object[order]= orders_type_total_amount

                return {
                    "designer_count": designer_count,
                    "online_designer_count": online_designer_count,
                    "today_order_count": today_order_count,
                    "today_order_total_amount": today_order_total_amount,
                    "today_finalized_order_total_count": today_finalized_order_total_count,
                    "today_finalized_order_total_amount": today_finalized_order_total_amount,
                    "ordered_total_count": ordered_total_count,
                    "pending_orders_count": pending_orders_count,
                    "ongoing_orders_count": ongoing_orders_count,
                    "unconfirmed_assignment_count": unconfirmed_assignment_count,
                    "order_type_object": order_type_object,
                    "order_type_total_amount_object": order_type_total_amount_object,
                    "order_count_of_mouth_object" : order_count_of_mouth_object,
                    "order_amount_of_mouth_object" : order_amount_of_mouth_object,
                    "finalized_order_count_of_mouth_object" : finalized_order_count_of_mouth_object,
                    "finalized_order_amount_of_mouth_object" : finalized_order_amount_of_mouth_object,
                    "order_of_mouth_object" : order_of_mouth_object,
                    "mouth_list" : mouth_list
                }


    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))





@Router.post("/upload_user_avatar_image")
async def upload_user_avatar_image(user_id:str=Form(...),role:str=Form(...),image_data:UploadFile=File(...)):
    try:
        image_url = await upload_image_to_upyun(image_data, "/image/user_avatar_image/")
        logger.info(f"Upload user avatar 1111 {image_url}")
        with Session(engine) as session, session.begin():
            if role=="designer":
                query_table = session.query(DesignerRegisterTable).filter(DesignerRegisterTable.user_id == user_id)
            elif role=="admin":
                query_table = session.query(AdministratorTableBase).filter(AdministratorTableBase.user_id == user_id)
            query_table.update({"user_avatar_url":image_url})
        return {
            "user_avatar_image_url":image_url
        }

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"上传失败：{str(e)}")


@Router.post("/delete_user_avatar_image_url")
async def delete_user_avatar_image_url(old_image_url=Body(embed=True)):
    try:
        logger.info(f"Upload user avatar 1111 {old_image_url}")
        image_url = old_image_url.replace("mt-web-data.test.upcdn.net/","")
        await delete_image_to_upyun(image_url)
        logger.info(f"Upload user avatar 2222 {image_url}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除：{str(e)}")
