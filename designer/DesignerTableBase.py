from decimal import Decimal

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, create_engine, DECIMAL, Float, Boolean
from sqlalchemy.orm import Session,  Mapped, mapped_column, relationship
from datetime import datetime


from core.TableBase import Base


class DesignerRegisterTable(Base):
    __tablename__ = "designer_register_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    gender: Mapped[str] = mapped_column(String(255), nullable=False, unique=False, index=True)
    cell_phone_number: Mapped[str] = mapped_column(String(11), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    user_password: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_role: Mapped[str] = mapped_column(String(255), nullable=False, index=True, server_default="designer")
    professional_field: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    user_avatar_url: Mapped[str] = mapped_column(String(255), nullable=True,unique=True, server_default=None, default=None)
    registration_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    on_line_status:Mapped[bool] = mapped_column(Boolean, nullable=False, server_default='0',default=False, index=True)
    designer_rating: Mapped[int] = mapped_column(DECIMAL(3,2), nullable=False,default=4.50, server_default='4.50', index=True)
    completed_orders: Mapped[str] = mapped_column(String(100), nullable=False,server_default='0',index=True)

    bank_card_number: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    alipay_account: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    withdrawable_amount: Mapped[Decimal] = mapped_column(DECIMAL(5, 0), nullable=False, default=Decimal('0.00'), index=True)
    total_income: Mapped[Decimal] = mapped_column(DECIMAL(5, 0), nullable=False, default=Decimal('0.00'), index=True)
    id_card_no: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)

    supervisor_id: Mapped[str] = mapped_column(ForeignKey("administrator_info.user_id", ondelete='SET NULL'), nullable=True)
    administratorTableBase=relationship('AdministratorTableBase', back_populates="designerRegisterTable", passive_deletes=True, lazy="selectin" )
    orderTableBase=relationship('OrderTableBase', back_populates="designerRegisterTable", passive_deletes=True)

    designerWithdrawApplicationTable=relationship('DesignerWithdrawApplicationTable', back_populates="designerTableBase", passive_deletes=True, lazy="selectin")

    works_table_base=relationship("WorksTableBase", back_populates="designer_table", passive_deletes=True, lazy="selectin")

    order_notification = relationship("OrderNotificationTableBase", back_populates="designer_parent", passive_deletes=True, lazy="selectin")

    def __repr__(self):
        return f"{self.id} {self.user_id} {self.user_name} {self.professional_field} {self.supervisor_id} {self.administratorTableBase}"
#
# class DesignerAccountTableBase(Base):
#     __tablename__ = "designer_account_table_base"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
#     balance_after: Mapped[Decimal] = mapped_column(DECIMAL(5, 0), nullable=False, default=Decimal('0.00'), index=True)
#     designer_id:Mapped[str] = mapped_column(String(100), nullable=False, index=True , server_default="8620251116")
#     order_id:Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
#     transaction_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True, server_default="")
#     change_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 0), nullable=False, default=Decimal('0.00'), server_default="0.00", index=True)
#     change_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

