import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("Migrating...")
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR(50);"))
        except Exception as e:
            print("phone_number column might already exist", e)
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN address TEXT;"))
        except Exception as e:
            print("address column might already exist", e)
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT FALSE NOT NULL;"))
        except Exception as e:
            print("is_approved column might already exist", e)
        print("Migration complete")

if __name__ == "__main__":
    asyncio.run(migrate())
