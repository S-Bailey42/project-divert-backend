from fastapi import HTTPException

from http import HTTPStatus


cannot_find_email_password = HTTPException(
    HTTPStatus.UNAUTHORIZED, 
    detail="cannot find email and/or password"
)
Incorrect_email_password = HTTPException(
    status_code=HTTPStatus.UNAUTHORIZED,
    detail="Incorrect email or password",
    headers={"WWW-Authenticate": "Bearer"},
)
incorrect_level_of_access = HTTPException(
    HTTPStatus.UNAUTHORIZED, 
    detail="you do not have access.",
    headers={"WWW-Authenticate": "Bearer"},
)
def Invaild_value(name: str, value):
    return HTTPException(
        HTTPStatus.NOT_FOUND,
        detail=f"{name} has an invalid value of {value}"
    )