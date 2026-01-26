from datetime import datetime,timedelta,UTC

from fastapi import APIRouter, Header, Depends, HTTPException, status,Response,Body
from sqlalchemy.orm import Session

from core.CreateEngine import engine
from designer.DesignerTableBase import DesignerRegisterTable
from designer.DesignerModels import DesignerSearchResponseModel

from .AdministratorTableBase import AdministratorTableBase
from .AdministratorModels import AdministratorLoginModel,AdministratorResponseModel
from core.security import pwd_passlib,jwt_token_key
import jwt
router = APIRouter()



@router.post("/login")
def login(response: Response, user: AdministratorLoginModel=Body(...)):
    print(user.role,223232323232)
    with Session(engine) as session, session.begin():
        if user.role == "admin":
            table_base = AdministratorTableBase
            responses_model=AdministratorResponseModel
        elif user.role == "designer":
            table_base = DesignerRegisterTable
            responses_model = DesignerSearchResponseModel
        login_info: table_base | None= session.query(table_base).filter_by(user_name=user.user_name).first()

        if login_info:
            if pwd_passlib.verify(user.user_password, login_info.user_password):
                jwt_token = jwt.encode(payload={"user_id": login_info.user_id, "exp": datetime.now(UTC) + timedelta(hours=1), "role":user.role},key=jwt_token_key,algorithm="HS256")
                response.headers["authorization"] = f"Bearer {jwt_token}"
                responses_user_data = responses_model.model_validate(login_info)
                return {
                    "user_info":responses_user_data
                }
            else:
                raise HTTPException(status_code=401,detail="用户名或密码错误2")
        else:
            raise HTTPException(status_code=401, detail="用户名或密码错误1")