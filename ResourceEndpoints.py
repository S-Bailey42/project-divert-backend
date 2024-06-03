



from fastapi import APIRouter
import db as Table
from api import DBSession
from sqlalchemy import select

Router = APIRouter(prefix="/resource", tags=["resource"])

@Router.get("/userTypes")
async def get_user_types(db_session: DBSession):
    return (
        await db_session.execute(
            select(Table.UserType).where(
                Table.UserType.Name != "Admin")
            )
        ).scalars().all()
