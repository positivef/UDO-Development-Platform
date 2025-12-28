import asyncio
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv(".env")


async def test():
    dsn = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    try:
        conn = await asyncpg.connect(dsn)
        await conn.close()
        print("SUCCESS")
    except Exception as e:
        print("FAIL", e)


asyncio.run(test())
