from fastapi import FastAPI, APIRouter, Depends
from pydantic import BaseModel,Field
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import expectionTypes
from api import *
import asyncio
import dbTypes
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from sqlalchemy import select
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


SECRET_KEY = "915589d3081478a34902d6a9454bfbfda1de3ce24f19f20d64ec3015b5d65adb982fc42470ed0fa6ac5060fbeb30346b8f192210295d828a7e2918c187e5dd27"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# defining routers

WorkSiteRouter = APIRouter(prefix="/worksite")
AuthRouter = APIRouter(prefix="/auth")
UserRouter = APIRouter(prefix="/user")
RequestRouter = APIRouter(prefix="/request")
ItemsRouter = APIRouter(prefix="/items")

EMAIL_re = r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$" 

class Token(BaseModel):
    access_token: str
    token_type: str

class requestAccountModel(BaseModel):
    companyName: str
    email: str = Field(pattern=EMAIL_re)
    userType: str

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

@RequestRouter.post("/account")
@limiter.limit("5/minute")
async def requestAccount(request: Request, data: requestAccountModel, db_session: DBSession):
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
async def viewRequests(admin: AdminUser, db_session: DBSession):
    req = await db_session.execute(select(Table.RequestAccount))
    return req.scalars().all()


@RequestRouter.post("/reject")
async def rejectRequest(admin: AdminUser, id: str, db_session: DBSession):
    # find request
    request = await db_session.get(Table.RequestAccount, id)
    if not request:
        #raise error here
        return
    await db_session.delete(request)
    await db_session.commit()

@RequestRouter.post("/accept")
async def acceptRequest(admin: AdminUser, id: str, db_session: DBSession):
    request = await db_session.get(Table.RequestAccount, id)
    if not request:
        #raise error here
        return
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

@RequestRouter.post("/add-item")
async def addNewItem(newItem: dbTypes.newItemModel, db_session: DBSession):
    item_type_validator = await db_session.get(Table.ItemType, newItem.itemTypeID)
    if not item_type_validator:
        return "Item Type does not exist"

    new_item = Table.Item(
        Name=newItem.name,
        SiteID=newItem.siteID,
        ItemTypeID=newItem.itemTypeID,
        Quantity=newItem.quantity,
        KGperItem=newItem.kgPerItem,
        Carbon=newItem.carbon, Dimensions=newItem.dimensions)
    
    db_session.add(new_item)
    await db_session.commit()
    await db_session.refresh(new_item)
    return Table.to_dict(new_item)

@RequestRouter.delete("/remove-item/{item_id}")
async def deleteItem(item_id: str, db_session: DBSession):
    request = await db_session.get(Table.Item, int(item_id))
    if not request:
        #raise error here
        return
    
    await db_session.delete(request)
    await db_session.commit()

    return "deleted"

@RequestRouter.post("/add-item-type")
async def addNewItemType(newItemType: str , db_session: DBSession):
    new_item_type =Table.ItemType(
        Name=newItemType
    )

    db_session.add(new_item_type)
    await db_session.commit()
    await db_session.refresh(new_item_type)
    return Table.to_dict(new_item_type)

@RequestRouter.post("/add-site")
async def addNewSite(newSite: dbTypes.newSiteModel, db_session: DBSession):
    new_site = Table.Site(
        Coordinates= newSite.Coordinates,
        Address= newSite.Address,
        Postcode= newSite.Postcode,
        SiteManager= newSite.SiteManager,
        PhoneNumber= newSite.PhoneNumber,
        Email= newSite.Email,
        StartDate= newSite.StartDate, 
        EndDate= newSite.EndDate
    )

    db_session.add(new_site)
    await db_session.commit()
    await db_session.refresh(new_site)
    return Table.to_dict(new_site)

@ItemsRouter.get("")
async def displayItems():
    return "works"





app.include_router(WorkSiteRouter)
app.include_router(AuthRouter)
app.include_router(UserRouter)
app.include_router(RequestRouter)
app.include_router(ItemsRouter)
