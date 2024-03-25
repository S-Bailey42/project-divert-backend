from fastapi import HTTPException

from http import HTTPStatus


cannot_find_email_password = HTTPException(
    HTTPStatus.NOT_FOUND, "cannot find email and/or password"
)
Incorrect_email_password = HTTPException(
    status_code=HTTPStatus.UNAUTHORIZED,
    detail="Incorrect email or password",
    headers={"WWW-Authenticate": "Bearer"},
)
