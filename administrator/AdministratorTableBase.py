from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, create_engine, DECIMAL
from sqlalchemy.orm import Session,  Mapped, mapped_column, relationship
from sqlalchemy import text
from datetime import datetime

from core.TableBase import Base

class AdministratorTableBase(Base):
    __tablename__ = "administrator_info"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    cell_phone_number: Mapped[str] = mapped_column(String(11), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    user_password: Mapped[str] = mapped_column(String(255), nullable=False, unique=False)
    user_role: Mapped[str] = mapped_column(String(255), nullable=False, index=True, server_default="admin")
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    user_avatar_url: Mapped[str] = mapped_column(String(255), nullable=True, unique=True, server_default=None, default=None)
    registration_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    orderTableBase=relationship("OrderTableBase", back_populates="administratorTableBase", passive_deletes=True, lazy='selectin')
    designerRegisterTable=relationship("DesignerRegisterTable",back_populates="administratorTableBase",passive_deletes=True, lazy='selectin')
    def __repr__(self):
        return f"{self.id} {self.name} {self.user_name} {self.user_id}"