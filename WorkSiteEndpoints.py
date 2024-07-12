

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from api import DBSession
from auth import ConstructionUser
import expectionTypes
import db as Table
import dbTypes
import config
from sanitize_filename import sanitize




Router = APIRouter(prefix="/worksite", tags=["Worksite"])
#things this router needs for it to be fully working
# able to add, delete, update and update items to a work site
# able to delete items from work site
# able to create 


@Router.post("/add/item")
async def add_item_to_work_site(
    user: ConstructionUser, 
    newItem: dbTypes.newItemModel, 
    db_session: DBSession):
    item_type_validator = await db_session.get(Table.ItemType, newItem.ItemTypeID)
    if not item_type_validator:
        return "Item Type does not exist"

    Site = await db_session.get(Table.Site, newItem.SiteID)
    
    if not Site:
        raise expectionTypes.Invalid_value("siteID", newItem.SiteID)
    
    if Site.UserID != user.id:
        raise expectionTypes.incorrect_level_of_access
     
    #check if site has the same user id
    new_item = Table.Item(
        Name=newItem.Name,
        SiteID=newItem.SiteID,
        ItemTypeID=newItem.ItemTypeID,
        Quantity=newItem.Quantity,
        KgPerItem=newItem.KgPerItem,
        Carbon=newItem.Carbon, 
        Dimensions=newItem.Dimensions,
        Taken=newItem.Taken
    )
    
    db_session.add(new_item)
    await db_session.commit()
    await db_session.refresh(new_item)
    return Table.to_dict(new_item)

@Router.delete("/remove/item")
async def delete_item_from_worksite(user: ConstructionUser, item_id: str, db_session: DBSession):
    request = await db_session.get(Table.Item, int(item_id))
    if not request:
        raise expectionTypes.Invaild_value("item_id", item_id)
    Site = await db_session.get(Table.Site, request.SiteID)

    if not Site:
        raise expectionTypes.Invaild_value("siteID", request.SiteID)

    if Site.UserID != user.id:
        raise expectionTypes.incorrect_level_of_access
    
    await db_session.delete(request)
    await db_session.commit()

    return 

@Router.post("/add/item/image")
async def add_images_to_item(item_id: int, db_session: DBSession, files: list[UploadFile] = File(...)):
    #check if item_id is real
    item_obj = await db_session.get(Table.Item, item_id)
    if not item_obj:
        raise expectionTypes.Invaild_value("item_id", item_id)

    for file in files:
        try:
            file_name = sanitize(file.filename)
            new_image = Table.Image(ItemID = item_id, name = file_name)
            db_session.add(new_image)
            await db_session.commit()
            await db_session.refresh(new_image)

            contents = file.file.read()
            with open(f"{config.IMAGE_SRC}/{new_image.id}-{new_image.ItemID}-{file_name}", 'wb') as f:
                f.write(contents)
            
        except Exception:
            return {"message": "There was an error uploading the file(s)"}
        finally:
            file.file.close()
    #return [file.filename for file in files]




@Router.post("/create")
async def create_worksite(user: ConstructionUser, newSite: dbTypes.newSiteModel, db_session: DBSession):
    new_site = Table.Site(
        UserID = user.id,
        SiteName = newSite.SiteName,
        Coordinates= newSite.Coordinates,
        Address= newSite.Address,
        Postcode= newSite.Postcode,
        SiteManager= newSite.SiteManager,
        PhoneNumber= newSite.PhoneNumber,
        IsActive= True,
        StartDate= newSite.StartDate, 
        EndDate= newSite.EndDate,
    )

    db_session.add(new_site)
    await db_session.commit()
    await db_session.refresh(new_site)
    return Table.to_dict(new_site)



@Router.delete("/delete")
async def delete_worksite(user: ConstructionUser, worksite_id: str, db_session: DBSession):
    Site = await db_session.get(Table.Site, worksite_id)

    if not Site:
        raise expectionTypes.Invaild_value("siteID", worksite_id)

    if Site.UserID != user.id:
        raise expectionTypes.incorrect_level_of_access
    await db_session.delete(Site)
    await db_session.commit()
    return
    
@Router.get("/mySites")
async def get_my_worksite(user: ConstructionUser, db_session: DBSession):
    query = await db_session.execute(select(Table.Site).filter_by(UserID=user.id))
    return query.scalars().all()
#todo: improve to allow non ConstructionUsers to access
@Router.get("")
async def get_worksite(user: ConstructionUser, db_session: DBSession, worksite_id: str):
    Site = await db_session.get(Table.Site, worksite_id)
    if not Site:
        raise expectionTypes.Invaild_value("worksite_id", worksite_id)
    if Site.UserID != user.id:
        raise expectionTypes.incorrect_level_of_access
    return Site

@Router.get("/items/{site_id}")
async def get_site_items(
    user: ConstructionUser,
    site_id: str,
    db_session: DBSession
):
    #check if site exists and belongs to the user
    site = await db_session.execute(select(Table.Site).filter_by(UserID=user.id, id=site_id))
    siteObject = site.scalars().first()

    if not siteObject:
        raise expectionTypes.Invalid_value("site_id", site_id)
    
    #Query for items on the site
    items = await db_session.execute(select(Table.Item).filter_by(SiteID=site_id))
    items_list = items.scalars().all()

    return [Table.to_dict(item) for item in items_list]