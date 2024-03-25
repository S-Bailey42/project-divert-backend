from fastapi import FastAPI, APIRouter, Depends
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

# defining routers

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


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], 
    session: DBSession
):
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

LoginUserInfo = Annotated[dbTypes.User, Depends(get_current_user)]


async def admin_user(
    user: LoginUserInfo,
    session: DBSession
):
    userType = (await session.get(Table.UserType, user.UserTypeID))
    
    if userType:
        if userType.Name.lower() != "admin":
            raise expectionTypes.incorrect_level_of_access
    else:
        raise expectionTypes.Invaild_value("UserTypeID", user.UserTypeID)

AdminUser = Annotated[dbTypes.User, Depends(admin_user)]
#RequireAdmin = Annotated[dbTypes.User, Depends(get_current_user)]


@UserRouter.get("/about")
async def About_user(user: LoginUserInfo):
    return user


@AuthRouter.post("/login")
async def loginUser(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db_session: DBSession
):

    if not (
        await authenticate_user(db_session, form_data.username, form_data.password)
    ):
        raise expectionTypes.Incorrect_email_password

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

# Just to note here, the return of this function is the user's password 
# which will not be shown again to the admin.
# TODO: the database and api needs to be updated to surport this.
# On first time login, it will require the user to reset the password
@AuthRouter.post("/signup")
async def createUser(
    newUser: dbTypes.NewUser,
    admin: AdminUser,
    db_session: DBSession
):
    return await create_account(
        session=db_session,
        user_obj=newUser
        )


app.include_router(WorkSiteRouter)
app.include_router(AuthRouter)
app.include_router(UserRouter)
