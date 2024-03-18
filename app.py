from fastapi import FastAPI,APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import expectionTypes
from api import *
import asyncio
import dbTypes
app = FastAPI()
SECRET_KEY = "915589d3081478a34902d6a9454bfbfda1de3ce24f19f20d64ec3015b5d65adb982fc42470ed0fa6ac5060fbeb30346b8f192210295d828a7e2918c187e5dd27"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

#defining routers

WorkSiteRouter = APIRouter(prefix="/worksite")
AuthRouter = APIRouter(prefix="/auth")
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

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: DBSession):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise expectionTypes.Incorrect_email_password
    except JWTError:
        raise expectionTypes.Incorrect_email_password
    user = await get_user_by_email(username, session)
    if user is None:
        raise expectionTypes.Incorrect_email_password
    return user

@UserRouter.get("/about")
async def About_user(user: Annotated[dbTypes.User, Depends(get_current_user)]):
    return user


@AuthRouter.post("/login")
async def Login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db_session: DBSession):
    
    if not (await authenticate_user(db_session, form_data.username, form_data.password)):
        raise expectionTypes.Incorrect_email_password
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
    #return access_token_expires

@AuthRouter.post("/signup")
async def Signup_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db_session: DBSession):
    pass
    #if  (await check_if_user_exists(form_data.username)):
    #    raise HTTPException(HTTPStatus.BAD_REQUEST, "Invaild email")



app.include_router(WorkSiteRouter)
app.include_router(AuthRouter)
app.include_router(UserRouter)
