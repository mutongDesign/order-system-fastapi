from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

pwd_passlib=CryptContext(schemes=["argon2"], deprecated="auto")
jwt_token_key='QYrz_xueyuan-12*'

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")