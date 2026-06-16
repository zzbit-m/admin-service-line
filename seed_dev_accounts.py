import asyncio
from app.db.session import async_session_local
from app.models.user import User
from app.models.request import ServiceRequest
from app.models.attachment import Attachment
from app.models.resource import Resource
from app.core.security import hash_password
from sqlalchemy import select

async def seed():
    async with async_session_local() as session:
        for email, role in [("user@test.com", "user"), ("admin@test.com", "admin")]:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            hpass = hash_password("testpass")
            if user:
                user.role = role
                user.hashed_password = hpass
                print(f"Updated user {email} to role {role}")
            else:
                user = User(email=email, hashed_password=hpass, role=role)
                session.add(user)
                print(f"Created user {email} with role {role}")
        await session.commit()

if __name__ == "__main__":
    asyncio.run(seed())
