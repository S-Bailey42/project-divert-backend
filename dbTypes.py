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
    name: str
    siteID: str
    itemTypeID: int
    quantity: int
    kgPerItem: int
    carbon: Optional[int] = 0
    dimensions: str

class newSiteModel(BaseModel):
    Coordinates: str
    Address: str
    Postcode: str
    SiteManager: str
    IsActive: bool
    PhoneNumber: str
    StartDate: datetime
    EndDate: Optional[datetime]