import db as Table
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from fastapi.encoders import jsonable_encoder
from fastapi import Depends, HTTPException
from typing import Annotated
import contextlib
from typing import Any, AsyncIterator
from sqlalchemy import select
import hashing
import asyncio
from http import HTTPStatus
import secrets
from typing import Optional
import dbTypes
def passwordGen() -> str:
    return secrets.token_urlsafe(16)


class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any] = {}):
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine)

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        async with sessionmanager._engine.begin() as connection:
            await connection.run_sync(Table.Base.metadata.create_all)
        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")
        async with sessionmanager._engine.begin() as connection:
            await connection.run_sync(Table.Base.metadata.create_all)
        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager("sqlite+aiosqlite:///./app.db")


async def get_db_session():
    async with sessionmanager.session() as session:
        yield session


DBSession = Annotated[AsyncSession, Depends(get_db_session)]


async def check_if_user_exists(email: str, session: AsyncSession) -> bool:
    stmt = select(Table.User).where(Table.User.Email == email)
    ret = (await session.execute(stmt)).scalar()
    if ret:
        return True
    return False


async def create_account(session: AsyncSession, user_obj: dbTypes.NewUser, password: Optional[str] = None):
    if not password:
        password = passwordGen()
    if await check_if_user_exists(user_obj.Email, session):
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Invaild email")

    if not (await session.get(Table.UserType, user_obj.UserTypeID)):
        raise HTTPException(HTTPStatus.NOT_FOUND, "cannot find userType")

    pw_hash = hashing.password(password)
    new_user = Table.User(Email=user_obj.Email, UserTypeID=user_obj.UserTypeID)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    session.add(Table.Password(id=new_user.id, Content=pw_hash))
    await session.commit()
    await session.refresh(new_user)
    return {**Table.to_dict(new_user), "password":password}


async def get_user_by_email(email: str, session: AsyncSession) -> Table.User:
    stmt = select(Table.User).where(Table.User.Email == email)
    ret = (await session.execute(stmt)).scalar()
    if ret == None:
        raise HTTPException(HTTPStatus.NOT_FOUND, "cannot find email and/or password")

    return ret


async def authenticate_user(db_session: AsyncSession, email: str, pw: str):
    user_obj = await get_user_by_email(email, db_session)

    password_obj = await db_session.get(Table.Password, user_obj.id)
    if password_obj == None:
        raise HTTPException(HTTPStatus.NOT_FOUND, "cannot find email and/or password")
    return hashing.check(pw, password_obj.Content)


# asyncio.run(main())
