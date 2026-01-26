from pydantic import BaseModel, ConfigDict, field_validator
from administrator.AdministratorModels import AdministratorResponseModel
from designer.DesignerModels import DesignerSearchResponseModel


class WorksImageResponseTableBase(BaseModel):
    id:int
    work_id: str
    image_url: str
    sort_num: int

    model_config = ConfigDict(from_attributes=True)


class WorkResponseModels(BaseModel):
    id:int
    work_id: str
    work_name: str
    work_type: str
    work_intro: str|None
    works_status: int
    create_time: str
    update_time: str
    cover_url: str
    designer_id: str
    download_permission: int
    visibility_status: int

    designer_table:DesignerSearchResponseModel
    works_image_tableBase:list[WorksImageResponseTableBase]

    model_config = ConfigDict(from_attributes=True)

    @field_validator('create_time', mode='before')
    @classmethod
    def convert_create_time(cls, value):
        return value.strftime('%Y-%m-%d')

    @field_validator('update_time', mode='before')
    @classmethod
    def convert_update_time(cls, value):
        return value.strftime('%Y-%m-%d')