

from fastapi import APIRouter, File, UploadFile
from api import DBSession
from auth import ConstructionUser
import expectionTypes
import db as Table
import dbTypes


Router = APIRouter(prefix="/worksite", tags=["Worksite"])



@Router.post("/add/item")
async def add_item_to_work_site(
    user: ConstructionUser, 
    newItem: dbTypes.newItemModel, 
    db_session: DBSession):
    item_type_validator = await db_session.get(Table.ItemType, newItem.itemTypeID)
    if not item_type_validator:
        return "Item Type does not exist"

    Site = await db_session.get(Table.Site, newItem.siteID)
    
    if not Site:
        raise expectionTypes.Invaild_value("siteID", newItem.siteID)
    
    if Site.UserID != user.id:
        raise expectionTypes.incorrect_level_of_access
     
    #check if site has the same user id
    new_item = Table.Item(
        Name=newItem.name,
        SiteID=newItem.siteID,
        ItemTypeID=newItem.itemTypeID,
        Quantity=newItem.quantity,
        KGperItem=newItem.kgPerItem,
        Carbon=newItem.carbon, 
        Dimensions=newItem.dimensions
        )
    
    db_session.add(new_item)
    await db_session.commit()
    await db_session.refresh(new_item)
    return Table.to_dict(new_item)

@Router.post("/add/item/image")
async def add_images_to_item(item_id: int, db_session: DBSession, files: list[UploadFile] = File(...)):
    #check if item_id is real

    for file in files:
        try:
            new_image = Table.Image(ItemID = item_id)
            db_session.add(new_image)
            await db_session.commit()
            await db_session.refresh(new_image)

            contents = file.file.read()
            with open(f"{new_image}-{file.filename}", 'wb') as f:
                f.write(contents)
            
        except Exception:
            return {"message": "There was an error uploading the file(s)"}
        finally:
            file.file.close()
    return [file.filename for file in files]

@Router.delete("/remove/item")
async def delete_item_from_worksite(user: ConstructionUser, item_id: str, db_session: DBSession):
    request = await db_session.get(Table.Item, int(item_id))
    if not request:
        raise expectionTypes.Invaild_value("item_id", item_id)
    
    Site = await db_session.get(Table.Site, request.siteID)

    if not Site:
        raise expectionTypes.Invaild_value("siteID", request.siteID)
    
    if Site.UserID != user.id:
        raise expectionTypes.incorrect_level_of_access
    
    await db_session.delete(request)
    await db_session.commit()

    return 


@Router.post("/create")
async def create_worksite(user: ConstructionUser, newSite: dbTypes.newSiteModel, db_session: DBSession):
    new_site = Table.Site(
        UserID = user.id,
        Coordinates= newSite.Coordinates,
        Address= newSite.Address,
        Postcode= newSite.Postcode,
        SiteManager= newSite.SiteManager,
        PhoneNumber= newSite.PhoneNumber,
        IsActive= True,
        StartDate= newSite.StartDate, 
    )

    db_session.add(new_site)
    await db_session.commit()
    await db_session.refresh(new_site)
    return Table.to_dict(new_site)

@Router.delete("/delete")
async def delete_worksite(user: ConstructionUser,worksite_id: str, db_session: DBSession):
    pass