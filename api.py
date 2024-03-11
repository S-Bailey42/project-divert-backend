import db as Table
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from fastapi import Depends
from typing import Annotated
import contextlib
from typing import Any, AsyncIterator
from sqlalchemy import select
import hashing
import asyncio
#Base.metadata.create_all(engine)

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

        session = self._sessionmaker()
        try:
            

            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager("sqlite+aiosqlite:///./hello.db")

async def get_db_session():
    async with sessionmanager.session() as session:
        yield session

DBSession = Annotated[AsyncSession, Depends(get_db_session)]



async def get_user_by_email(email: str, session: AsyncSession) -> Table.User:
    return None




async def authenticate_user(email: str, pw: str):
    async with sessionmanager.session() as session:
        user_obj = await get_user_by_email(email, session)
        if user_obj == None:
            return None
        password_obj = await session.get(Table.Password, user_obj.id)
        if password_obj == None:
            return None 
        return hashing.check(pw, password_obj.Content)
        
        


async def main():
    Table.Base.metadata.bind = sessionmanager._engine
    async with sessionmanager._engine.begin() as connection:
        await connection.run_sync(Table.Base.metadata.create_all)

asyncio.run(main())