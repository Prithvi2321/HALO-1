from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.auth.controller import router as auth_router
from app.research.controller import router as research_router, submit_query, UniversalQueryInput
from app.audit.controller import router as audit_router
from app.drafting.controller import router as drafting_router
from app.workspace.controller import router as workspace_router
from app.telegram.controller import router as telegram_router
from app.news.controller import router as news_router
from app.generation.controller import router as legacy_drafts_router
from app.auth.repository import init_db, engine
from app.workspace.seed import seed_workspace_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        with Session(engine) as session:
            seed_workspace_data(session)
    except Exception as e:
        print(f"[Startup] Seed notice: {e}")
    yield


app = FastAPI(
    title="HALO Legal Research & Practice Management API",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Permissive CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers under /api/v1 (and root aliases)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(auth_router)
app.include_router(research_router, prefix="/api/v1")
app.include_router(research_router, prefix="/api")
app.include_router(research_router)
app.include_router(audit_router, prefix="/api/v1")
app.include_router(audit_router)
app.include_router(drafting_router, prefix="/api/v1")
app.include_router(drafting_router)
app.include_router(workspace_router, prefix="/api/v1")
app.include_router(workspace_router)
app.include_router(telegram_router, prefix="/api/v1")
app.include_router(telegram_router)
app.include_router(news_router, prefix="/api/v1")
app.include_router(news_router)
app.include_router(legacy_drafts_router, prefix="/api/v1/legacy")


@app.post("/api/query", tags=["research"])
@app.post("/query", tags=["research"])
def api_query_alias(req: UniversalQueryInput):
    return submit_query(req)


@app.get("/api/v1/health", tags=["system"])
@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok", "version": "2.1.0", "framework": "HALO-NyayaSahayak"}
