from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: str
    Name: Optional[str]
    CharityNumber: Optional[int]
    Email: str
    UserTypeID: int
    PhoneNumber: Optional[str]

class NewUser(BaseModel):
    Name: str
    Email: str
    CharityNumber: Optional[int]
    UserTypeID: int
    PhoneNumber: Optional[str]


class newItemModel(BaseModel):
    Name: str
    SiteID: str
    ItemTypeID:int 
    Quantity: int 
    KgPerItem: int 
    Carbon: int
    Dimensions: str 
    Taken: bool


class ItemModel(BaseModel):
    id: int
    Name: str
    SiteID: str
    ItemTypeID: int
    Quantity: int
    KgPerItem: int
    Carbon: int = 0
    Dimensions: str
    Taken: bool = False

class newSiteModel(BaseModel):
    Coordinates: str
    Address: str
    Postcode: str
    SiteManager: str
    IsActive: bool
    PhoneNumber: str
    StartDate: Optional[datetime]
    EndDate: Optional[datetime]
    SiteName: str