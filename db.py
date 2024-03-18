from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, DateTime, Boolean,ForeignKey, BLOB
from uuid import uuid4
from sqlalchemy import create_engine
import asyncio
Base = declarative_base()


#def _fk_pragma_on_connect(dbapi_con, con_record):
#    dbapi_con.execute('pragma foreign_keys=ON')

#from sqlalchemy import event
#event.listen(engine, 'connect', _fk_pragma_on_connect)

def gen_uuid():
    return str(uuid4())



#async def async_main():
#    engine = create_async_engine(
#        "sqlite+asyncpg://scott:tiger@localhost/test",
#    )








# api for userType table
# user with any auth:
#   GET: read whole table
#   
# Admin auth: 
#   POST: Add new usertype
#   DELETE: usertype
# 
# 
# 


class UserType(Base): #
    __tablename__ = "UserType"
    id = Column(Integer, primary_key=True)
    Name = Column(String)



# api for user table
# normal User auth:
#   GET: Your own user info
#   DELETE: Their own account
#   PATCH: Change the following of your info:
#       Name, Email and PhoneNumber
#      
# Admin auth: 
#   GET: All user info
#   DELETE: any user.
#   POST: create a user.
#   PATCH: Change any user info
#   
#  
# 

class User(Base): #
    __tablename__ = "User"
    id = Column(String, primary_key=True, default=gen_uuid)
    Name = Column(String)
    CharityNumber = Column(Integer)
    Email = Column(String)
    UserTypeID = Column(Integer, ForeignKey("UserType.id")) # 
    PhoneNumber = Column(String)
    userType = relationship('UserType', foreign_keys='User.UserTypeID')


# api for Site table
# user with any auth:
#   GET: any site info
# Users with Charity UserType auth:
#   POST: register interest on items on a site
# Users with worker UserType auth:
#   POST: create a new site
#   PATCH: Add items to site
#   DELETE: their own sites.
# Admin auth: 
#   DELETE: any site.
# 
# 
# 

class Site(Base): #
    __tablename__ = "Site"
    id = Column(String, primary_key=True, default=gen_uuid)
    UserID = Column(String, ForeignKey("User.id"))
    Coordinates = Column(String)
    Address = Column(String)
    Postcode = Column(String)
    SiteManager = Column(String)
    PhoneNumber = Column(String)
    Email = Column(String)
    StartDate = Column(DateTime(timezone=True))
    EndDate = Column(DateTime(timezone=True))

    user = relationship('User', foreign_keys='Site.UserID')

# api for password table
# User auth:
#   PATCH: change your password
#   


class Password(Base): #
    __tablename__ = "Password"
    id = Column(String, ForeignKey("User.id"), primary_key=True)
    Content = Column(BLOB)

    user = relationship('User', foreign_keys='Password.id')


# api for user table
# User auth:
#   
#   
# Admin auth: 
#   
# 
# 
# 

class ItemType(Base): #
    __tablename__ = "ItemType"
    id = Column(Integer, primary_key=True)
    Name = Column(String)



# api for user table
# User auth:
#   
#   
# Admin auth: 
#   
# 
# 
# 

class Item(Base): #
    __tablename__ = "Item"
    id = Column(Integer, primary_key=True)
    Name = Column(String)
    SiteID = Column(String, ForeignKey("Site.id")) # 
    ItemTypeID = Column(Integer, ForeignKey("ItemType.id")) # 
    Taken = Column(Boolean)
    Quantity = Column(Integer)
    KGperItem = Column(Integer)
    Carbon = Column(Integer)
    Dimensions = Column(String)

    site = relationship('Site', foreign_keys='Item.SiteID')
    itemType = relationship('ItemType', foreign_keys='Item.ItemTypeID')





class ItemInterest(Base):
    __tablename__ = "ItemInterest"
    id = Column(Integer, primary_key=True)
    ItemID = Column(Integer, ForeignKey("Item.id"))
    UserID = Column(String, ForeignKey("User.id"))
    IsInterested = Column(Boolean)
    item = relationship('Item', foreign_keys='ItemInterest.ItemID')
    user = relationship('User', foreign_keys='ItemInterest.UserID')






#Base.metadata.create_all(engine)