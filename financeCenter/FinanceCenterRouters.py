from datetime import datetime
from http.client import responses

import jwt

from alembic.util import status
from fastapi import APIRouter, Body, Path, HTTPException
from fastapi.openapi.utils import status_code_ranges
from sqlalchemy import func, select, insert
from sqlalchemy.orm import selectinload

ROUTER = APIRouter()

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from core.CreateEngine import engine, async_engine

from .FinanceCenterModels import RequestFinanceCenterModel, WithdrawalAlipayModel,ResponsesFinanceCenterModel
from designer.DesignerTableBase import DesignerRegisterTable
from designer.DesignerModels import DesignerSearchResponseModel
from order.OrderTableBase import OrderTableBase
from order.OrderModels import OrderSearchResponseModel
from .FinanceCenterTableBase import DesignerWithdrawApplicationTable, DesignerAccountTableBase
from administrator import AdministratorTableBase

from core.security import jwt_token_key

import os, hashlib

import logging
logger = logging.getLogger("uvicorn")

@ROUTER.get("/v1/withdrawal_application_statistics/designer/{designer_id}")
async def designer_withdrawal_application_statistics(designer_id: str=Path(...)):
    logger.info(f"财务查询信息:{designer_id}")

    async with AsyncSession(async_engine) as session:
        async with session.begin():
            matched_designer_result = await session.execute(select(DesignerRegisterTable).filter(DesignerRegisterTable.user_id == designer_id))
            designer=matched_designer_result.scalar_one_or_none()
            responses_designer = DesignerSearchResponseModel.model_validate(designer)
            logger.info(f"设计师信息:{designer}")

            # 查询所有申请记录表
            withdrawal_application_result = await session.execute(
                select(DesignerWithdrawApplicationTable)
                .options(
                    selectinload(DesignerWithdrawApplicationTable.designerTableBase)
                ))

            withdrawal_application = withdrawal_application_result.scalars().all()

            logger.info(f"777777777777777{withdrawal_application}")

            responses_withdrawal_application =[ResponsesFinanceCenterModel.model_validate(value) for value in withdrawal_application]

            pending_payout_amount_result = await session.execute(select(func.sum(DesignerWithdrawApplicationTable.applied_amount)).filter(DesignerWithdrawApplicationTable.designer_id == designer_id, DesignerWithdrawApplicationTable.payment_status == 0))
            pending_payout_amount = pending_payout_amount_result.scalar()

            if pending_payout_amount is None:
                pending_payout_amount = 0

            unsettled_amount_sum_result = await session.execute(
                select(func.sum(OrderTableBase.amount)).filter(OrderTableBase.designer_id == designer_id,
                                                               OrderTableBase.accounting_status == "未入账"))

            unsettled_amount_sum = unsettled_amount_sum_result.scalar()

            matched_withdrawal_application_result=await session.execute(select(func.sum(DesignerWithdrawApplicationTable.applied_amount)).filter(
                DesignerWithdrawApplicationTable.designer_id == designer_id,
                DesignerWithdrawApplicationTable.payment_status == 0,
                ))

            withdrawal_application = matched_withdrawal_application_result.scalar()
            logger.info(f'111111111111111{withdrawal_application}')
            if withdrawal_application:
                balance=designer.withdrawable_amount-withdrawal_application
            else:
                balance=designer.withdrawable_amount

            logger.info(f"可用余额:{balance}")
        return {
            "responses_designer":responses_designer ,
            "responses_withdrawal_application": responses_withdrawal_application,
            "balance": balance,
            "unsettled_amount": unsettled_amount_sum,
            "pending_payout_amount": pending_payout_amount,
        }





# 生成随机码
def gen_random_code():
    machine_id = os.getenv("MACHINE_ID", "A1")
    rand_bytes = os.urandom(2)
    return f"{machine_id}{hashlib.sha256(rand_bytes).hexdigest()[:2]}"

# 生成校验码返回A-Z的一个字母
def luhn_check(code:str):
    total = 0
    for i,char in enumerate(code):
        num = int(char,36)
        total += num * (2 if i %2 == 0 else 1)
    return chr(65 + total % 26)


@ROUTER.post("/v1/withdrawals")
async def v1_withdrawals(request_data:WithdrawalAlipayModel=Body(...)):

    try:
        async with AsyncSession(async_engine) as session:
            async with session.begin():
                logger.info(f"申请提现信息:{request_data.designer_id}")

                matched_designer_result = await session.execute(select(DesignerRegisterTable).filter(DesignerRegisterTable.user_id == request_data.designer_id))

                designer =  matched_designer_result.scalar_one_or_none()

                prefix = "WD"
                date_str = datetime.now().strftime("%y%m%d")
                random_code = gen_random_code()
                base_code = f"{prefix}-{date_str}-{random_code}"
                check_digit = luhn_check(base_code.replace("-", ""))
                full_id = f"{base_code.upper()}-{check_digit.upper()}"

                if request_data.payment_mode=="支付宝":
                    designer_payment_account=designer.alipay_account
                elif request_data.payment_mode=="银行卡":
                    designer_payment_account = designer.bank_card_number
                else:
                    designer_payment_account = ""
                logger.info(f"设计师支付方式:{designer_payment_account}")
                withdrawal_application_table_object={
                    "withdrawal_application_no" : full_id,
                    "designer_id" : request_data.designer_id,
                    "applied_amount" : request_data.applied_amount,
                    "payment_mode" : request_data.payment_mode,
                    "payment_account" : designer_payment_account,
                    "service_fee" : 0,
                }

                await session.execute(insert(DesignerWithdrawApplicationTable).values(withdrawal_application_table_object))

            return {
                "responses_text": "创建成功"
            }
    except Exception as e:
        logger.error(e)

# 查询为打款的申请表
@ROUTER.get("/v1/withdrawal-applications/admin/{admin_id}/pending")
async def list_admin_pending_withdrawal_application(admin_id:str=Path(...)):

    try:
        async with AsyncSession(async_engine) as session:
            async with session.begin():
                logger.info(f"申请提现信息:{admin_id}")
                admin_result =await session.execute(select(AdministratorTableBase).filter(AdministratorTableBase.user_id == admin_id))
                matched_admin = admin_result.scalar_one_or_none()
                if not matched_admin:
                    raise HTTPException(status_code=401, detail="无权限")

                designer_pending_withdrawal_application_result=await session.execute(
                    select(DesignerWithdrawApplicationTable)
                    .options(selectinload(DesignerWithdrawApplicationTable.designerTableBase))
                    .filter(DesignerWithdrawApplicationTable.payment_status == 0)
                )
                matched_applications=designer_pending_withdrawal_application_result.scalars().all()
                logger.info(matched_applications)

                responses_query_finance_center_table=[ResponsesFinanceCenterModel.model_validate(data) for data in matched_applications]

            return {
                "responses_data": responses_query_finance_center_table,
            }
    except Exception as e:
        logger.error(e)

# 查询已打款申请
@ROUTER.get("/v1/withdrawal-applications/admin/{admin_id}/comment")
async def list_admin_comment_withdrawal_application(admin_id:str=Path(...)):

    try:
        async with AsyncSession(async_engine) as session:
            async with session.begin():
                logger.info(f"申请提现信息:{admin_id}")
                admin_result =await session.execute(select(AdministratorTableBase).filter(AdministratorTableBase.user_id == admin_id))
                matched_admin = admin_result.scalar_one_or_none()
                if not matched_admin:
                    raise HTTPException(status_code=401, detail="无权限")

                designer_pending_withdrawal_application_result=await session.execute(
                    select(DesignerWithdrawApplicationTable)
                    .options(selectinload(DesignerWithdrawApplicationTable.designerTableBase))
                    .filter(DesignerWithdrawApplicationTable.payment_status == 1)
                )
                matched_applications=designer_pending_withdrawal_application_result.scalars().all()
                logger.info(matched_applications)

                responses_query_finance_center_table=[ResponsesFinanceCenterModel.model_validate(data) for data in matched_applications]

            return {
                "responses_data": responses_query_finance_center_table,
            }
    except Exception as e:
        logger.error(e)

# 更改为打款完成
@ROUTER.patch("/v1/withdrawal-applications/admin/{admin_id}/{withdrawal_application_no}/complete-payment")
async def admin_change_withdrawal_application_payment_status(admin_id:str=Path(...),withdrawal_application_no:str=Path(...)):

    try:
        async with AsyncSession(async_engine) as session:
            async with session.begin():
                logger.info(f"申请提现信息:{admin_id}")
                admin_result =await session.execute(select(AdministratorTableBase).filter(AdministratorTableBase.user_id == admin_id))
                matched_admin = admin_result.scalar_one_or_none()
                if not matched_admin:
                    raise HTTPException(status_code=401, detail="无权限")

                designer_pending_withdrawal_application_result=await session.execute(
                    select(DesignerWithdrawApplicationTable)
                    .options(selectinload(DesignerWithdrawApplicationTable.designerTableBase))
                    .filter(DesignerWithdrawApplicationTable.withdrawal_application_no == withdrawal_application_no)
                )
                matched_applications=designer_pending_withdrawal_application_result.scalar_one_or_none()

                matched_applications.payment_status=1
                matched_applications.designerTableBase.withdrawable_amount=matched_applications.designerTableBase.withdrawable_amount-matched_applications.applied_amount

                new_designer_account={
                    "balance_after":matched_applications.designerTableBase.withdrawable_amount,
                    "designer_id":matched_applications.designer_id,
                    "transaction_type":"提现",
                    "change_amount":-matched_applications.applied_amount,
                }

                await session.execute(
                    insert(DesignerAccountTableBase).values(new_designer_account)
                )

            return {
                "status":200,
                "msg":"打款状态修改成功"
            }
    except Exception as e:
        logger.error(e)

# 查询所有提现申请数据
@ROUTER.get("/v1/withdrawal-applications-statistics/admin/{admin_id}")
async def admin_withdrawal_application_statistics(admin_id:str=Path(...)):
    try:
        async with AsyncSession(async_engine) as session:
            async with session.begin():
                logger.info(f"申请提现信息:{admin_id}")

                # 待处理的申请
                pending_withdrawal_application_result= await session.execute(
                    select(DesignerWithdrawApplicationTable)
                    .options(
                        selectinload(DesignerWithdrawApplicationTable.designerTableBase)
                    )
                    .filter(DesignerWithdrawApplicationTable.payment_status == 0))
                pending_withdrawal_application=pending_withdrawal_application_result.scalars().all()
                pending_withdrawal_application_count=len(pending_withdrawal_application)

                responses_pending_withdrawal_application = [ResponsesFinanceCenterModel.model_validate(data) for data in
                                                            pending_withdrawal_application]
                responses_pending_withdrawal_application_count = pending_withdrawal_application_count

                 # 已处理的申请
                comment_withdrawal_application_result= await session.execute(
                    select(DesignerWithdrawApplicationTable)
                    .options(
                        selectinload(DesignerWithdrawApplicationTable.designerTableBase)
                    )
                    .filter(DesignerWithdrawApplicationTable.payment_status == 1))
                comment_withdrawal_application=comment_withdrawal_application_result.scalars().all()
                comment_withdrawal_application_count=len(comment_withdrawal_application)

                responses_comment_withdrawal_application=[ResponsesFinanceCenterModel.model_validate(data) for data in comment_withdrawal_application]
                responses_comment_withdrawal_application_count=comment_withdrawal_application_count

                total_amount_paid_result= await session.execute(
                    select(func.sum(DesignerWithdrawApplicationTable.applied_amount))
                    .filter(DesignerWithdrawApplicationTable.payment_status == 1)
                )
                total_amount_paid=total_amount_paid_result.scalar_one_or_none()

                if total_amount_paid:
                    responses_total_amount_paid=total_amount_paid
                else:
                    responses_total_amount_paid=0

            return {
                "responses_pending_withdrawal_application": responses_pending_withdrawal_application,
                "responses_pending_withdrawal_application_count": responses_pending_withdrawal_application_count,
                "responses_comment_withdrawal_application": responses_comment_withdrawal_application,
                "responses_comment_withdrawal_application_count": responses_comment_withdrawal_application_count,
                "responses_total_amount_paid": responses_total_amount_paid,
            }

    except Exception as e:
        logger.error(e)