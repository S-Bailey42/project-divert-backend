


from types import SimpleNamespace
from typing import Annotated
from fastapi import APIRouter, Depends
from auth import AdminUser, create_token
import expectionTypes
from api import DBSession, authenticate_user, create_account
from basicauth import decode
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import dbTypes
Router = APIRouter(prefix="/auth", tags=["Auth"])


class Authbody(BaseModel):
    username: str
    password: str

@Router.post("/login/form")
async def loginUser(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db_session: DBSession
):

    if not (
        await authenticate_user(db_session, form_data.username, form_data.password)
    ):
        raise expectionTypes.Incorrect_email_password
    return create_token(form_data)

@Router.post("/login")
async def loginUser(
    form_data: Authbody, db_session: DBSession
):

    if not (
        await authenticate_user(db_session, form_data.username, form_data.password)
    ):
        raise expectionTypes.Incorrect_email_password
    return create_token(form_data)

# Just to note here, the return of this function is the user's password 
# which will not be shown again to the admin.
# TODO: the database and api needs to be updated to surport this.
# On first time login, it will require the user to reset the password
@Router.post("/signup")
async def create_User(
    newUser: dbTypes.NewUser,
    admin: AdminUser,
    db_session: DBSession
):
    return await create_account(
        session=db_session,
        user_obj=newUser
        )

@Router.post("/login/basic")
async def Login_with_basic_auth(basic: str, db_session: DBSession):
    try:
        username, password = decode(basic)
    except:
        raise expectionTypes.Invaild_value("basic", basic)
    if not (
        await authenticate_user(db_session, username, password)
    ):
        raise expectionTypes.Incorrect_email_password
    return create_token(SimpleNamespace(username = username))