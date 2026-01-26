from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from .TableBase import Base
from financeCenter.FinanceCenterTableBase import DesignerWithdrawApplicationTable, DesignerAccountTableBase
from designer.DesignerTableBase import DesignerRegisterTable
from order.OrderTableBase import OrderTableBase
from administrator.AdministratorTableBase import AdministratorTableBase
from works.WorksTableBase import WorksTableBase, WorksImageTableBase

engine = create_engine('mysql+pymysql://root:12345@127.0.0.1:3306/test_one', echo=True)
async_engine = create_async_engine('mysql+aiomysql://root:12345@127.0.0.1:3306/test_one', echo=False, pool_pre_ping=True, pool_size=10, max_overflow=10)



Base.metadata.create_all(engine)