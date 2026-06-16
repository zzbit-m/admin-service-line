import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:admin123@localhost:5432/admin_portal")
    rows = await conn.fetch("SELECT email, role, full_name FROM users ORDER BY created_at")
    if not rows:
        print("No users found in database.")
    for r in rows:
        print(dict(r))
    await conn.close()

asyncio.run(main())
