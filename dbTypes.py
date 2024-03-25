from pydantic import BaseModel
from typing import Optional


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
