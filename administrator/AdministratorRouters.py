from fastapi import APIRouter, Form, HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from core.CreateEngine import engine

from administrator.AdministratorTableBase import AdministratorTableBase
from core.security import pwd_passlib

router = APIRouter()

@router.post("/administrator_register")
def administrator_register(
        name: str = Form(...),
        age: int = Form(...),
        cell_phone_number: str = Form(...),
        email: str = Form(...),
        user_name: str = Form(...),
        user_password: str = Form(...),
        user_id: str = Form(...),
):

    hash_user_password=pwd_passlib.hash(user_password)
    try:
        with Session(engine) as session, session.begin():
            session.add(AdministratorTableBase(
                name=name,
                age=age,
                cell_phone_number=cell_phone_number,
                email=email, user_name=user_name,
                user_password=hash_user_password,
                user_id=user_id))
            return '成功l'
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")