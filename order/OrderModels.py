from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, field_validator

from administrator.AdministratorModels import AdministratorResponseModel
from designer.DesignerModels import DesignerSearchResponseModel

app = FastAPI()


# 订单创建验证model
class OrderCreateModel(BaseModel):
    order_id: str
    order_type: str
    order_title: str
    supervisor_id: str
    order_status: str
    order_overview: str
    order_deadline: datetime
    order_amount:Decimal


class OrderSearchResponseModel(BaseModel):
    id: int
    order_id: str
    order_type: str
    order_title: str
    supervisor_id: str
    designer_id: str|None
    order_status: str
    accounting_status: bool
    order_overview: str
    created_at: str
    assign_at:str|None
    delivery_deadline: str
    approved_at: str|None
    amount: int
    administratorTableBase: AdministratorResponseModel | None
    designerRegisterTable: DesignerSearchResponseModel | None
    model_config = ConfigDict(from_attributes=True)

    @field_validator('delivery_deadline', mode='before')
    @classmethod
    def validate_delivery_deadline(cls, value):
        return value.strftime('%Y-%m-%d %H:%M')

    @field_validator('created_at', mode='before')
    @classmethod
    def validate_created_at(cls, value):
        return value.strftime('%Y-%m-%d %H:%M')

    @field_validator('assign_at', mode='before')
    @classmethod
    def validate_assign_at(cls, value):
        if value is not None:
            return value.strftime('%Y-%m-%d %H:%M')
        else:
            return None

    @field_validator('approved_at', mode='before')
    @classmethod
    def validate_approved_at(cls, value):
        if value is not None:
            return value.strftime('%Y-%m-%d %H:%M')
        else:
            return None





# 订单修改验证model
class OrderUpDateModel(BaseModel):
    order_id: str|None=None
    order_type: Optional[Literal['待分配','待查收','查收超时','进行中','已完成','已退款','已取消']]|None=None,
    order_title: str|None=None
    supervisor_id: str|None=None
    designer_id: str|None=None
    order_status: str|None=None
    accounting_status: bool|None=None
    order_overview: str|None=None
    order_deadline: datetime|None=None
    amount:Decimal|None=None
    change_item:dict|None=None

# 订单通知验证model
class OrderNotificationModel(BaseModel):
    notification: str|None=None
    delivery_status: int|None=None
    is_read: bool|None=None
    sent_at: str|None=None
    designer_id: str|None=None
    order_id: str|None=None
    model_config = ConfigDict(from_attributes=True)

    @field_validator('sent_at', mode='before')
    @classmethod
    def validate_sent_at(cls, value):
        return value.strftime('%Y-%m-%d %H:%M')