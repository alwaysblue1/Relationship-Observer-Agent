from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import upload, analysis, integrations, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Relationship Observer API",
    description="一个不会替你定义关系，只帮助你看见变化的 AI Observer。",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(integrations.router)
app.include_router(auth.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Relationship Observer"}
