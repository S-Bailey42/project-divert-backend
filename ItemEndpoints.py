
from fastapi import APIRouter
from sqlalchemy import select
import db as Table
from api import DBSession
from auth import AdminUser, LoginUserInfo
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import Page, add_pagination
from dbTypes import ItemModel
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



@Router.get("", response_model=Page[ItemModel])
async def display_Items(user: LoginUserInfo ,db_session: DBSession) -> Page[ItemModel]:
    userTypeCheck = await db_session.get(Table.UserType, user.UserTypeID)
    if not userTypeCheck.Name:
        raise NotImplementedError()
    elif userTypeCheck.Name == "Construction":
        site = await db_session.execute(select(Table.Site).filter_by(UserID=user.id))
        siteObject = site.scalars().first()
        if not siteObject:
            return None
        siteId = siteObject.id
        #siteItems = await db_session.execute(select(Table.Item).filter_by(SiteID=siteId))
        return await paginate(db_session, select(Table.Item).filter_by(SiteID=siteId))
        #return siteItems.scalars().all()
    elif userTypeCheck.Name == "Beneficiary":
        return await paginate(db_session, select(Table.Item))
        #req = await db_session.execute(select(Table.Item))
        #return req.scalars().all()
    else:
        return await paginate(db_session, select(Table.Item))
    
