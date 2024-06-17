from api import *
import json
import asyncio
import db
import pathlib
import os
import dbTypes
import config 
async def main():
    db_file = "./app.db"
    sessionmanager = DatabaseSessionManager(f"sqlite+aiosqlite:///{db_file}")
    if pathlib.Path(db_file).is_file():
        os.remove(db_file)
    async with sessionmanager._engine.begin() as connection:
        await connection.run_sync(Table.Base.metadata.create_all)

    userTypes = ("Construction", "Beneficiary", "Admin")
    itemTypes = (
        "lumber",
        "bricks",
        "cement",
        "metal",
        "roofing materials",
        "insulation", 
        "fasteners", 
        "hand tools", 
        "power tools", 
        "paint", 
        "plumbing supplies", 
        "electrical supplies", 
        "lighting", 
        "windows", 
        "doors", 
        "flooring",
        "carpeting",
        "piping",
        "masonry",
        "drywall",
        "aggregates",
        "safety gear",
        "scaffolding",
        "unused materials",
        "furniture",
        "chairs",
        "tables",
        "shelves",
        "cabinets",
        "storage solutions",
        "bed frames",
        "mattresses",
        "sofas"
        )
    with open("accounts.json", "r") as f:
        accounts = json.load(f)

    async with sessionmanager.session() as session:
        for t in userTypes:
            session.add(db.UserType(Name=t))
        for t in itemTypes:
            session.add(db.ItemType(Name=t))
        await session.commit()
        for acc in accounts:
            acc_obj = dbTypes.NewUser(
                Name=acc["name"],
                Email=acc["email"],
                CharityNumber = None,
                UserTypeID = acc["type"],
                PhoneNumber = None
            ) 
            await create_account(session, acc_obj, acc["password"])
    if pathlib.Path(f"./{config.IMAGE_SRC}").is_dir():
        os.remove(config.IMAGE_SRC)
    os.mkdir(config.IMAGE_SRC)

if __name__ == "__main__":
    asyncio.run(main())