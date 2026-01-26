from datetime import datetime
from decimal import Decimal

from sqlalchemy.dialects.mysql import TINYINT

from core.TableBase import Base
from sqlalchemy import Column, Integer, String, DateTime, JSON, Numeric, DECIMAL, func, text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column

# 提现申请表
class DesignerWithdrawApplicationTable(Base):
    __tablename__ = 'designer_withdraw_application'
    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    designer_id: Mapped[str] = mapped_column(ForeignKey("designer_register_table.user_id", ), nullable=False,unique=False)
    withdrawal_application_no : Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    designerTableBase=relationship('DesignerRegisterTable', back_populates="designerWithdrawApplicationTable", passive_deletes=True, lazy='selectin' )

    applied_amount:Mapped[Decimal] = mapped_column(DECIMAL(10,2), nullable=False, index=True,default=Decimal('0.00'),server_default='0.00')
    payment_mode:Mapped[str] = mapped_column(String(255), nullable=False,index=True)
    payment_account: Mapped[str] = mapped_column(String(255), nullable=False, unique=False)
    service_fee:Mapped[Decimal] = mapped_column(DECIMAL(10,2), nullable=False, index=True, default=Decimal('0.00'),server_default='0.00')
    apply_time:Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True, server_default=func.now())
    payment_status:Mapped[int] = mapped_column(TINYINT, nullable=False, index=True,server_default='0',default=0,comment="0=申请中,1=已打款, 2=驳回")
    # related_order_ids:Mapped[list[str]] = mapped_column(JSON, nullable=False, index=True, default=list,server_default=text("(JSON_ARRAY())"))


# 设计师资金变动表
class DesignerAccountTableBase(Base):
    __tablename__ = "designer_account_table_base"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    balance_after: Mapped[Decimal] = mapped_column(DECIMAL(5, 0), nullable=False, default=Decimal('0.00'), index=True)
    designer_id:Mapped[str] = mapped_column(String(100), nullable=False, index=True , server_default="8620251116")
    order_id:Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True, server_default="")
    change_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 0), nullable=False, default=Decimal('0.00'), server_default="0.00", index=True)
    change_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())