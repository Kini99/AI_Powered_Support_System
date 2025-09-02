from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from backend.app.core.config import settings
from backend.app.api.auth.routes import router as auth_router
from backend.app.api.tickets.routes import router as tickets_router
from backend.app.api.admin.routes import router as admin_router

app = FastAPI(
    title="Masai LMS Support System",
    description="Intelligent support system with multi-agentic RAG",
    version="1.0.0",
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://intelligent-lms-support-ppfz.vercel.app"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    same_site="none",   
    https_only=True 
)

# Include routers
app.include_router(auth_router, prefix="/v1/auth", tags=["Authentication"])
app.include_router(tickets_router, prefix="/v1/tickets", tags=["Tickets"])
app.include_router(admin_router, prefix="/v1/admin", tags=["Admin"])

@app.get("/")
async def root():
    return {
        "message": "Masai LMS Support System API",
        "version": "1.0.0",
        "status": "running",
        "database": "MongoDB + Redis + Pinecone"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "MongoDB"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)