
from fastapi import APIRouter
from sqlalchemy import select
import db as Table
from api import DBSession
from auth import AdminUser, LoginUserInfo


Router = APIRouter(prefix="/items", tags=["Items"])




@Router.post("/add/type")
async def add_Item_Type(admin: AdminUser, name: str , db_session: DBSession):

    stmt = select(Table.ItemType).where(Table.ItemType.Name == name)
    if (await db_session.execute(stmt)).scalar_one_or_none():
        return "Item type already exist"

    new_item_type = Table.ItemType(
        Name=name
    )

    db_session.add(new_item_type)
    await db_session.commit()
    await db_session.refresh(new_item_type)
    return Table.to_dict(new_item_type)



@Router.get("")
async def display_Items(user: LoginUserInfo ,db_session: DBSession):
    userTypeCheck = await db_session.get(Table.UserType, user.UserTypeID)
    if not userTypeCheck.Name:
        return "Something went wrong"
    elif userTypeCheck.Name == "Construction":
        site = await db_session.execute(select(Table.Site).filter_by(UserID=user.id))
        siteObject = site.scalars().first()
        siteId = siteObject.id
        siteItems = await db_session.execute(select(Table.Item).filter_by(SiteID=siteId))
        return siteItems.scalars().all()
    elif userTypeCheck.Name == "Beneficiary":
        req = await db_session.execute(select(Table.Item))
        return req.scalars().all()