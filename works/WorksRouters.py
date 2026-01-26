import math
import uuid

from fastapi import APIRouter, UploadFile, File, Body, Form, HTTPException, Query
from sqlalchemy import insert, func
from sqlalchemy.orm import Session, selectinload

from order import OrderTableBase

ROUTER = APIRouter()

import logging
logger = logging.getLogger("uvicorn")

from core.CreateEngine import engine
from administrator.AdministratorTableBase import AdministratorTableBase
from designer.DesignerTableBase import DesignerRegisterTable
from  works.WorksTableBase import WorksTableBase, WorksImageTableBase
from .WorkModels import WorkResponseModels

from core.CloudAuth import upload_image_to_qcloud,upload_image_to_upyun




@ROUTER.post("/upload_work")
async def upload_work(
        user_id:str=Form(...),
        cover_file:UploadFile=File(...),
        work_title:str=Form(...),
        work_type:str=Form(...),
        work_intro:str=Form(...),
        files:list[UploadFile] =File(...),
        download_permission:bool=Form(...),
        visibility_status:bool=Form(...),
):
    try:
        work_id=uuid.uuid4().hex
        logger.info(user_id)
        logger.info(work_title)
        logger.info(work_type)
        logger.info(work_intro)
        cover_url=await upload_image_to_upyun(cover_file,f"/image/work_image/{work_id}/cover")
        logger.info(cover_url)

        with Session(engine) as session, session.begin():
            work_table_info=WorksTableBase(
                work_id=work_id,
                designer_id=user_id,
                work_name=work_title,
                work_type=work_type,
                work_intro=work_intro,
                cover_url=cover_url,
                download_permission=download_permission,
                visibility_status=visibility_status,
            )
            session.add(work_table_info)

            work_image_url_list=[
                {
                    "work_id":work_id,
                    "image_url":await upload_image_to_upyun(file,f"/image/work_image/{work_id}"),
                    "sort_num":index
                } for index,file in enumerate(files)
            ]

            logger.info(f"wwwwwwwwwwww{work_image_url_list}")
            session.execute(
                insert(WorksImageTableBase).values(work_image_url_list)
            )

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"上传失败：{str(e)}")


@ROUTER.get("/search/works")
async def search_works(
        works_type:str=Query(...),
        works_status:str=Query(...),
        works_create_time:str=Query(...),
        works_search_key_word:str=Query(...),
        user_id:str=Query(...),
        role:str=Query(...),
        active_page:str=Query(...),
):
    try:
        with Session(engine) as session, session.begin():
            if role != "admin":
                matched_works = session.query(WorksTableBase).options(selectinload(WorksTableBase.designer_table),selectinload(WorksTableBase.works_image_tableBase)).filter(WorksTableBase.designer_id==user_id)
            else:
                matched_works = session.query(WorksTableBase).options(selectinload(WorksTableBase.designer_table),selectinload(WorksTableBase.works_image_tableBase))

            total_works_count = matched_works.count()

            search_parameter_list=[]

            if works_type !="全部":
                search_parameter_list.append(WorksTableBase.work_type==works_type)
            if works_status !="全部":
                search_parameter_list.append(WorksTableBase.works_status == works_status)
            if works_create_time:
                search_parameter_list.append(WorksTableBase.create_time >=works_create_time)

            searched_works=matched_works.filter(*search_parameter_list).order_by(WorksTableBase.create_time.desc()).offset((int(active_page)-1)*10).limit(10).all()
            searched_works_count=len(searched_works)

            logger.info(searched_works[0].work_id)
            logger.info(1111111111111)
            logger.info(searched_works_count)

            searched_works_list=[WorkResponseModels.model_validate(value) for value in searched_works]

            total_pages=max(1,math.ceil(total_works_count/10))

            return {
                "totalPages":total_pages,
                "totalWorksCount":total_works_count,
                "searchedWorksCount":searched_works_count,
                "searchedWorksList":searched_works_list,
            }
    except Exception as e:
        logger.error(e)
