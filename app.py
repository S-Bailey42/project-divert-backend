from fastapi import FastAPI, APIRouter, Depends
from pydantic import BaseModel,Field
from typing import Annotated, List
from fastapi.security import OAuth2PasswordRequestForm
import expectionTypes
from api import *
import dbTypes
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from sqlalchemy import select
from auth import AdminUser, LoginUserInfo, create_token, ConstructionUser, BeneficiaryUser
from basicauth import decode
from types import SimpleNamespace
from fastapi import File, UploadFile


Image_location = "./images"

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
WorkSiteRouter = APIRouter(prefix="/worksite")
AuthRouter = APIRouter(prefix="/auth")
UserRouter = APIRouter(prefix="/user")
RequestRouter = APIRouter(prefix="/request")
ItemRouter = APIRouter(prefix="/items")

EMAIL_re = r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$" 
class requestAccountModel(BaseModel):
    companyName: str
    email: str = Field(pattern=EMAIL_re)
    userType: str

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
    return create_token(form_data)

# Just to note here, the return of this function is the user's password 
# which will not be shown again to the admin.
# TODO: the database and api needs to be updated to surport this.
# On first time login, it will require the user to reset the password
@AuthRouter.post("/signup")
async def create_User(
    newUser: dbTypes.NewUser,
    admin: AdminUser,
    db_session: DBSession
):
    return await create_account(
        session=db_session,
        user_obj=newUser
        )

@AuthRouter.post("/login/basic")
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

@RequestRouter.post("/account")
@limiter.limit("5/minute")
async def request_Account(request: Request, data: requestAccountModel, db_session: DBSession):
    #check if the email is in the user table
    stmt = select(Table.User).where(Table.User.Email == data.email)
    user_email_check = (await db_session.execute(stmt)).scalar()
    if user_email_check:
        return

    #check if the email is in the requestAccount table
    stmt = select(Table.RequestAccount).where(Table.RequestAccount.email == data.email)
    requestAccount_email_check = (await db_session.execute(stmt)).scalar()
    if requestAccount_email_check:
        return

    #check if the usertype is correct
    stmt = select(Table.UserType).where(Table.UserType.Name == data.userType)
    userType = (await db_session.execute(stmt)).scalar()

    if not userType:
        raise expectionTypes.Invaild_value("userType", data.userType)
    
    #if the userType is not either construction or beneficiary.
    allowed_accounts = ("Construction", "Beneficiary")
    if userType.Name not in allowed_accounts:
        raise expectionTypes.Invaild_value("userType", userType.Name) 
    
    db_session.add(
        Table.RequestAccount(
            companyName=data.companyName,
            email=data.email,
            userType=userType.id
        )
    )
    await db_session.commit()
    return 

@RequestRouter.get("/view")
async def view_Requests(admin: AdminUser, db_session: DBSession):
    req = await db_session.execute(select(Table.RequestAccount))
    return req.scalars().all()


@RequestRouter.post("/reject")
async def reject_Request(admin: AdminUser, id: str, db_session: DBSession):
    # find request
    request = await db_session.get(Table.RequestAccount, id)
    if not request:
        #raise error here
        return
    await db_session.delete(request)
    await db_session.commit()

@RequestRouter.post("/accept")
async def accept_Request(admin: AdminUser, id: str, db_session: DBSession):
    request = await db_session.get(Table.RequestAccount, id)
    if not request:
        raise expectionTypes.Invaild_value("id", id)
        
    new_user = dbTypes.NewUser(
        Name = request.companyName,
        Email = request.email,
        UserTypeID = request.userType,
        CharityNumber= None,
        PhoneNumber= None
    )
    ret = await create_account(db_session, new_user)
    await db_session.delete(request)
    await db_session.commit()
    return ret

@WorkSiteRouter.post("/add/item")
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

@WorkSiteRouter.post("/add/item/image")
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

@WorkSiteRouter.delete("/remove/item")
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

@ItemRouter.post("/add/type")
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

@WorkSiteRouter.post("/create")
async def create_worksite(user: ConstructionUser, newSite: dbTypes.newSiteModel, db_session: DBSession):
    new_site = Table.Site(
        UserID = user.id,
        Coordinates= newSite.Coordinates,
        Address= newSite.Address,
        Postcode= newSite.Postcode,
        SiteManager= newSite.SiteManager,
        PhoneNumber= newSite.PhoneNumber,
        IsActive= True,
        #Email= user.Email,
        StartDate= newSite.StartDate, 
    )

    db_session.add(new_site)
    await db_session.commit()
    await db_session.refresh(new_site)
    return Table.to_dict(new_site)

@WorkSiteRouter.delete("/delete")
async def delete_worksite(user: ConstructionUser,worksite_id: str, db_session: DBSession):
    pass

@ItemRouter.get("")
async def display_Items(db_session: DBSession):
    req = await db_session.execute(select(Table.Item))
    return req.scalars().all()

# UserRouter.post("/site/add")
# sync def add_worksite(user: ConstructionUser | BeneficiaryUser, db_session: DBSession, new_site: dbTypes.NEW):
#    user = await db_session.get(Table.User, newItem.siteID)
# 





app.include_router(WorkSiteRouter)
app.include_router(AuthRouter)
app.include_router(UserRouter)
app.include_router(RequestRouter)
app.include_router(ItemRouter)
