"""
Admin Dashboard Service

Standalone FastAPI application for the Ruko Admin Dashboard.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import API router
# Since this runs as top-level script in container, import directly
from api import close_db_pool, init_db_pool, router as admin_admin_router

app = FastAPI(title="Ruko Admin Dashboard")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API router
app.include_router(admin_admin_router)

# Mount static files if needed, but we serve dashboard.html from root
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Redirect root to dashboard."""
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard")
async def dashboard():
    """Serve the dashboard HTML."""
    static_path = Path(__file__).parent / "dashboard.html"
    if not static_path.exists():
        return {"error": "Dashboard file not found", "path": str(static_path)}
    return FileResponse(str(static_path), media_type="text/html")

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "ruko-admin"}


@app.on_event("startup")
def _startup():
    # Keep startup resilient: the UI can still load and surface DB errors gracefully.
    try:
        if os.getenv("ADMIN_DB_INIT_ON_STARTUP", "0") == "1":
            init_db_pool()
    except Exception:
        pass


@app.on_event("shutdown")
def _shutdown():
    try:
        close_db_pool()
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
