from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import challenges, executor, history, drafts

app = FastAPI(
    title="SQL Challenge API",
    description="API для генерации и проверки SQL задач",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

app.include_router(challenges.router, prefix="/api/challenges", tags=["challenges"])
app.include_router(executor.router, prefix="/api/executor", tags=["execute"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(drafts.router, prefix="/api/drafts", tags=["drafts"])


@app.get("/")
async def root():
    return {"message": "SQL Challenge API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
