import asyncio
from app.db.session import engine
from sqlalchemy import text

LINE_USER_ID = "Ub5d366082158f0fe3cde3d824e0ea449"

async def promote():
    async with engine.begin() as conn:
        result = await conn.execute(
            text("UPDATE users SET role = 'admin' WHERE line_user_id = :lid"),
            {"lid": LINE_USER_ID}
        )
        print(f"Updated {result.rowcount} row(s) — role set to admin")
        rows = await conn.execute(
            text("SELECT email, full_name, line_user_id, role FROM users WHERE line_user_id = :lid"),
            {"lid": LINE_USER_ID}
        )
        for r in rows:
            print(f"  → email={r[0]}  name={r[1]}  role={r[3]}")

asyncio.run(promote())
