
from pydantic import BaseModel, ConfigDict, field_validator, Field


# 管理员查询返回验证模型
class AdministratorResponseModel(BaseModel):
    id: int
    name: str
    age: int
    cell_phone_number:str
    email: str
    user_name: str
    user_password: str
    user_id: str
    user_avatar_url: str|None = Field(...)
    registration_date: str
    model_config = ConfigDict(from_attributes=True)

    @field_validator("registration_date", mode='before')
    @classmethod
    def validate_registration_date(cls, v):
        return v.strftime("%Y-%m-%d %H:%M")
    


# 管理员登录验证模型
class AdministratorLoginModel(BaseModel):
    user_name: str
    user_password: str
    role: str