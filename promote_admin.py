import sys
import asyncio
from app.db.session import engine
from sqlalchemy import text

async def promote(identifier: str):
    async with engine.begin() as conn:
        if identifier.startswith("U") and len(identifier) == 33:
            query = text("UPDATE users SET role = 'admin' WHERE line_user_id = :val")
        else:
            query = text("UPDATE users SET role = 'admin' WHERE email = :val")
            
        result = await conn.execute(query, {"val": identifier})
        print(f"Updated {result.rowcount} row(s) — role set to admin for '{identifier}'")
        
        rows = await conn.execute(
            text("SELECT email, full_name, line_user_id, role FROM users WHERE line_user_id = :val OR email = :val"),
            {"val": identifier}
        )
        for r in rows:
            print(f"  → email={r[0]}  name={r[1]}  line_id={r[2]}  role={r[3]}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python promote_admin.py <email_or_line_user_id>")
        sys.exit(1)
    asyncio.run(promote(sys.argv[1]))
