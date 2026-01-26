from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from administrator.AdministratorModels import AdministratorResponseModel

# 设计师注册验证model
class DesignerRegisterModel(BaseModel):
    name:str=Field(...)
    age: int = Field(..., ge=0, le=100)
    gender: str = Field(...)
    cellPhoneNumber: str = Field(...)
    email: EmailStr = Field(...)
    userName: str=Field(...)
    userPassword:str=Field(...)
    professionalField:str=Field(...)
    userId:str=Field(...)

# 设计师查询返回验证model
class DesignerSearchResponseModel(BaseModel):
    id: int
    name: str = Field(...)
    age: int = Field(..., ge=0, le=100)
    gender: str = Field(...)
    cell_phone_number: str = Field(...)
    email: EmailStr = Field(...)
    user_name: str = Field(...)
    user_password: str = Field(...)
    professional_field: str = Field(...)
    user_id: str = Field(...)
    user_avatar_url: str|None = Field(...)
    registration_date: str = Field(...)
    on_line_status:bool = Field(...)
    administratorTableBase: AdministratorResponseModel | None
    supervisor_id:str|None = Field(...)
    designer_rating: float = Field(...)
    completed_orders: str = Field(...)

    bank_card_number:str|None = Field(...)
    alipay_account:str|None = Field(...)

    withdrawable_amount:str = Field(...)
    total_income:str = Field(...)

    model_config = ConfigDict(from_attributes=True)

    @field_validator("registration_date", mode='before')
    @classmethod
    def validate_registration_date(cls, v):
        return v.strftime("%Y-%m-%d %H:%M")

    @field_validator("withdrawable_amount", mode='before')
    @classmethod
    def validate_withdrawable_amount(cls, v):
        return str(v)

    @field_validator("total_income", mode='before')
    @classmethod
    def validate_total_income(cls, v):
        return str(v)

