from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.core.arq_pool import create_arq_pool
from app.db.session import engine
from app.routers import admin, auth, auth_line, requests, attachments, resources, webhook

STATIC_DIR = Path(__file__).resolve().parent.parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    arq_pool = await create_arq_pool()
    app.state.arq_pool = arq_pool
    yield
    await arq_pool.close()
    await engine.dispose()

app = FastAPI(title="Admin Service Portal", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(requests.router)
app.include_router(admin.router)
app.include_router(attachments.router)
app.include_router(auth_line.router)
app.include_router(webhook.router)
app.include_router(resources.router)


@app.get("/liff-test.html")
@app.get("/liff-test")
async def liff_test():
    return FileResponse(STATIC_DIR / "liff-test.html")


@app.get("/liff-app.html")
@app.get("/liff-app")
async def liff_app():
    return FileResponse(STATIC_DIR / "liff-app.html")
