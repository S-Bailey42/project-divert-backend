


from datetime import datetime, timedelta, timezone
from typing import Annotated

from pydantic import BaseModel
from api import DBSession, get_user_by_email
import dbTypes
import db as Table
from jose import JWTError,jwt
import expectionTypes
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

SECRET_KEY = "915589d3081478a34902d6a9454bfbfda1de3ce24f19f20d64ec3015b5d65adb982fc42470ed0fa6ac5060fbeb30346b8f192210295d828a7e2918c187e5dd27"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


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

class PermissionSystem:
    def __init__(self, *users: str):
        self.users = users

    async def __call__(self, user: LoginUserInfo,session: DBSession):
        userType = (await session.get(Table.UserType, user.UserTypeID))
        if userType:
            if userType.Name not in self.users:
                raise expectionTypes.incorrect_level_of_access
        else:
            raise expectionTypes.Invaild_value("UserTypeID", user.UserTypeID)
    
class Token(BaseModel):
    access_token: str
    token_type: str

def create_token(form_data: OAuth2PasswordRequestForm) -> Token:
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

def permissionGroup(*users: str):
    return Annotated[dbTypes.User, Depends(PermissionSystem(*users))]

AdminUser = Annotated[dbTypes.User, Depends(PermissionSystem("Admin"))] 
BeneficiaryUser= Annotated[dbTypes.User, Depends(PermissionSystem("Beneficiary", "Admin"))] 
ConstructionUser = Annotated[dbTypes.User, Depends(PermissionSystem("Construction", "Admin"))]
