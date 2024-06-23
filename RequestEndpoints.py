

from emailServer import EmailSender
from fastapi import APIRouter, Request
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from sqlalchemy import select
import expectionTypes
from api import DBSession
from auth import AdminUser
import db as Table
import dbTypes
from slowapi.util import get_remote_address
from api import create_account
Router = APIRouter(prefix="/request", tags=["Request"])
limiter = Limiter(key_func=get_remote_address)


class requestAccountModel(BaseModel):
    companyName: str
    email: EmailStr
    userType: int



@Router.get("/view")
async def view_Requests(admin: AdminUser, db_session: DBSession):
    req = await db_session.execute(select(Table.RequestAccount))
    return req.scalars().all()


@Router.post("/reject")
async def reject_Request(admin: AdminUser, id: str, db_session: DBSession):
    # find request
    request = await db_session.get(Table.RequestAccount, id)
    if not request:
        #raise error here
        return
    await db_session.delete(request)
    await db_session.commit()

    email_obj = EmailSender(
        email='dovertproject@outlook.com',
        password='Divert@Project123',
        server='smtp.office365.com',
    )

    email_obj.send_email(
        request.email,
        "Encore Services - Account Request Rejected",
        f"""Dear {request.companyName},

Thank you for your interest in joining Project Divert. After careful consideration, we regret to inform you that your account request has been rejected. 

If you have any questions or need further assistance, please feel free to contact our support team at info@encore-environment.com.

Best regards,
Encore Services Team
"""
    )
    return{"detail": "Request rejected and email notification sent"}



@Router.post("/accept")
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



@Router.post("/account")
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
    #stmt = select(Table.UserType).where(Table.UserType.Name == data.userType)
    #userType = (await db_session.execute(stmt)).scalar()
    userType = await db_session.get(Table.UserType, data.userType)

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