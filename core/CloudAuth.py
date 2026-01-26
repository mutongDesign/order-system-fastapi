
import os
from fastapi import  HTTPException

import qiniu
import uuid

from qcloud_cos import CosConfig, CosS3Client

import upyun

from pydantic_settings import BaseSettings

import logging
logger = logging.getLogger("uvicorn")

QINIU_ACCESS_KEY = "r6Df3fI94p_EbJ6MvKl4MXlxQzB5SLXeQQ9cre63"

QINIU_SECRET_KEY = "_U3zIPVi9D_j9bZ1qAnHYmssejuLofCbOKmIPIEx"
QINIU_BUCKET_NAME = "mutongimage"
QINIU_DOMAIN = "t7r8hpgjp.hd-bkt.clouddn.com"

qiniu_auth=qiniu.Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
bucket = qiniu.BucketManager(qiniu_auth)

async def upload_user_avatar_to_qiniu(file,folder):
    try:
        file_ext = os.path.splitext(file.filename)[-1].lower()
        uuid_file_name = f"{folder}/{uuid.uuid4().hex}{file_ext}"
        logger.info(f"Upload user avatar {uuid_file_name}")
        file_content = await file.read()
        token = qiniu_auth.upload_token(QINIU_BUCKET_NAME,uuid_file_name,3600)
        ret,info=qiniu.put_data(token,uuid_file_name,file_content)
        logger.info(f"Upload file {info.status_code}")
        if info.status_code != 200:
            raise HTTPException(status_code=info.status_code,detail=info.text)
        return f"{QINIU_DOMAIN}/{uuid_file_name}"
    except Exception as e:
        logger.error(e)
        raise e

# 腾讯云配置
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_ID: str
    SECRET_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
settings = Settings()

REGION="ap-guangzhou"
BUCKET_NAME="mt-1258795762"
COS_DOMAIN="https://mt-1258795762.cos.ap-guangzhou.myqcloud.com"

config=CosConfig(
    Region=REGION,
    SecretId=settings.SECRET_ID,
    SecretKey=settings.SECRET_KEY,
    Scheme="https",

)
client = CosS3Client(config)
async def upload_image_to_qcloud(file, folder):
    try:
        file_ext = os.path.splitext(file.filename)[-1].lower()
        uuid_file_name = f"{folder}/{uuid.uuid4().hex}{file_ext}"
        logger.info(f"Upload user avatar 2222 {uuid_file_name}")
        file_content = await file.read()
        logger.info(f"Upload user avatar 333 {uuid_file_name}")
        logger.info(f"Received content_type: {file.content_type}")
        upload_result = client.put_object(
            Bucket=BUCKET_NAME,
            Key=uuid_file_name,
            Body=file_content,
            ContentType=file.content_type
        )
        logger.info(f"Upload file 555555 {upload_result}")
        return f"{COS_DOMAIN}/{uuid_file_name}"
    except Exception as e:
        logger.error(e)
        raise e

async def delete_image_to_qcloud(file_URL):
    try:
        client.delete_object(
            Bucket=BUCKET_NAME,
            Key=file_URL
        )
        logger.info(f"Upload file dddddddddddd ")
    except Exception as e:
        logger.error(e)
        raise e


upyun_service="mt-web-data"
upyun_user_name="mt360438600"
upyun_user_password="CfIS9KSFOjiqhs4lwFQi1fUtIhRnLip9"
upyun_domain="mt-web-data.test.upcdn.net"

up=upyun.UpYun(upyun_service,upyun_user_name,upyun_user_password)

async def upload_image_to_upyun(file, folder):
    try:
        file_ext = os.path.splitext(file.filename)[-1].lower()
        uuid_file_name = f"{folder}/{uuid.uuid4().hex}{file_ext}"
        logger.info(f"Upload user avatar 7777 {uuid_file_name}")

        file_content=b""
        while chunk := await file.read(1024):
            file_content+=chunk
        res = up.put(uuid_file_name,file_content)

        logger.info(f"Received content_type8888: {res}")

        return f"{upyun_domain}/{uuid_file_name}"
    except Exception as e:
        logger.error(e)
        raise e

async def delete_image_to_upyun(file_URL):
    try:
        up.delete(file_URL)
        logger.info(f"Upload file dddddddddddd ")
    except Exception as e:
        logger.error(e)
        raise e
