from datetime import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, func, text
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.TableBase import Base
class WorksTableBase(Base):
    __tablename__ = "works_table"
    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_id:Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    work_name:Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    work_type:Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    works_status:Mapped[int] = mapped_column(TINYINT, nullable=False, index=True, default=0, server_default="0", comment="0=待审核, 1=已发布, 2=已下架")
    work_intro:Mapped[str] = mapped_column(String(255), nullable=True,index=True)
    create_time:Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True, server_default=text('CURRENT_TIMESTAMP'))
    update_time:Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True, server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP') )
    cover_url:Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    designer_id:Mapped[str] = mapped_column(ForeignKey("designer_register_table.user_id", ondelete='SET NULL'), index=True, nullable=True)
    download_permission:Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    visibility_status:Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)

    designer_table=relationship("DesignerRegisterTable", back_populates="works_table_base", passive_deletes=True, lazy="selectin")
    works_image_tableBase = relationship('WorksImageTableBase', back_populates="works_table_base", passive_deletes=True, order_by="asc(WorksImageTableBase.sort_num)")

class WorksImageTableBase(Base):
    __tablename__ = "works_image_table"
    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_id:Mapped[str] = mapped_column(ForeignKey("works_table.work_id", ondelete="SET NULL"), index=True, nullable=True)
    works_table_base=relationship('WorksTableBase', back_populates="works_image_tableBase",passive_deletes=True, lazy="selectin")
    image_url:Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sort_num:Mapped[int] = mapped_column(Integer, nullable=False, index=True)