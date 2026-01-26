
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, create_engine, DECIMAL, Boolean
from sqlalchemy.orm import Session,  Mapped, mapped_column, relationship
from sqlalchemy import text
from sqlalchemy.dialects.mysql import INTEGER, TINYINT
from datetime import datetime

from core.TableBase import Base

class OrderTableBase(Base):
    __tablename__ = "order_info"
    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    order_type: Mapped[str] = mapped_column(String(100), nullable=False, unique=False, index=True)
    order_title: Mapped[str] = mapped_column(String(100), nullable=False, unique=False, index=True)
    order_status: Mapped[str] = mapped_column(String(100), nullable=False, unique=False, index=True)
    accounting_status: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True, server_default="0")
    order_overview: Mapped[str] = mapped_column(String(500), nullable=False, server_default="",  unique=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True, default=text('CURRENT_TIMESTAMP'))
    assign_at: Mapped[datetime|None] = mapped_column(DateTime, nullable=True, index=True,)
    delivery_deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True, server_default=func.now())
    approved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, index=True, )

    amount:Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    supervisor_id: Mapped[str] = mapped_column(ForeignKey("administrator_info.user_id", ondelete='SET NULL'), nullable=True, server_default='8620251115')
    administratorTableBase=relationship('AdministratorTableBase', back_populates="orderTableBase", passive_deletes=True,lazy="selectin")

    designer_id: Mapped[str|None] = mapped_column(ForeignKey("designer_register_table.user_id", ondelete='SET NULL'), nullable=True, server_default=None)
    designerRegisterTable=relationship('DesignerRegisterTable', back_populates="orderTableBase", passive_deletes=True,lazy="selectin")
    Order_notifications = relationship("OrderNotificationTableBase", back_populates="order_parent", passive_deletes=True,)

    def __repr__(self):
        return f"{self.id}{self.administratorTableBase.user_name}{self.order_id} {self.order_type} {self.order_title} {self.supervisor_id}"

class OrderNotificationTableBase(Base):
    __tablename__ = "order_notification"
    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    notification: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    delivery_status: Mapped[int] = mapped_column(TINYINT, nullable=False, index=True, comment="0=已推送, 1=用户已加载")
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True, server_default="0")
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True, default=datetime.now)

    designer_id:Mapped[str] = mapped_column(ForeignKey("designer_register_table.user_id", ondelete='SET NULL'), nullable=True, index=True)
    designer_parent =relationship("DesignerRegisterTable", back_populates="order_notification", passive_deletes=True,)

    order_id:Mapped[str] = mapped_column(ForeignKey("order_info.order_id", ondelete='SET NULL'), nullable=True, server_default=None)
    order_parent = relationship("OrderTableBase", back_populates="Order_notifications", passive_deletes=True,)
