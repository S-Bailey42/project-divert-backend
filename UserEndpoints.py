


from fastapi import APIRouter
from auth import LoginUserInfo


Router = APIRouter(prefix="/user", tags=["User"])

@Router.get("/about")
async def About_user(user: LoginUserInfo):
    return user