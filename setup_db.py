from api import *
import json
import asyncio
import db
import pathlib
import os
async def main():
    db_file = "./app.db"
    sessionmanager = DatabaseSessionManager(f"sqlite+aiosqlite:///{db_file}")
    if pathlib.Path(db_file).is_file():
        os.remove(db_file)
    async with sessionmanager._engine.begin() as connection:
        await connection.run_sync(Table.Base.metadata.create_all)
    
    userTypes = ("Worker","Charity", "Admin")
    with open("admin.json","r") as f:
        admin_json = json.load(f)


    async with sessionmanager.session() as session:
        for t in userTypes:
           session.add(db.UserType(Name=t))
        await session.commit()
        await create_account(
            session,
            "admin",
            3,
            admin_json["password"]
        )
        

if __name__ == "__main__":
    asyncio.run(main())



