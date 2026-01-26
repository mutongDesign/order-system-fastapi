from pydantic import BaseModel, field_validator, Field, ConfigDict
from designer.DesignerModels import DesignerSearchResponseModel

class RequestFinanceCenterModel(BaseModel):
    designer_id:str

class WithdrawalAlipayModel(BaseModel):
    designer_id:str|None = Field(default=None)
    applied_amount:int|None = Field(default=None)
    payment_mode:str|None = (Field(default=None))

class ResponsesFinanceCenterModel(BaseModel):
    id:int|None
    withdrawal_application_no:str|None
    applied_amount:str|None
    payment_mode:str|None
    payment_account:str|None
    service_fee:str|None
    designer_id:str|None
    designerTableBase:DesignerSearchResponseModel|None
    apply_time:str|None
    payment_status:int|None

    model_config = ConfigDict(from_attributes=True)

    @field_validator('applied_amount', mode="before")
    @classmethod
    def validate_applied_amount(cls, v):
        return str(v)

    @field_validator('apply_time', mode="before")
    @classmethod
    def validate_apply_time(cls, v):
        return v.strftime("%Y-%m-%d %H:%M")

    @field_validator('service_fee', mode="before")
    @classmethod
    def validate_service_fee(cls, v):
        return str(v)

