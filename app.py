from fastapi import FastAPI,APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
#from bcrypt import 
from api import *

app = FastAPI()
SECRET_KEY = "915589d3081478a34902d6a9454bfbfda1de3ce24f19f20d64ec3015b5d65adb982fc42470ed0fa6ac5060fbeb30346b8f192210295d828a7e2918c187e5dd27"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30



#defining routers

WorkSiteRouter = APIRouter(prefix="/site")
LoginRouter = APIRouter(prefix="/login")
UserRouter = APIRouter(prefix="/user")


class Token(BaseModel):
    access_token: str
    token_type: str



def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt




@LoginRouter.post("")
async def Login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return access_token_expires



app.include_router(WorkSiteRouter)
app.include_router(LoginRouter)
app.include_router(UserRouter)



if __name__ == "__main__":
    print(Table.UserType)