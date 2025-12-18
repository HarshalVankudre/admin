"""
Admin Dashboard Service

Standalone FastAPI application for the Ruko Admin Dashboard.
Provides a web UI and REST API for monitoring chatbot analytics.
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse

from .config import get_settings
from .database import close_pool, init_pool
from .routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    settings = get_settings()
    if settings.app.init_db_on_startup:
        try:
            init_pool()
        except Exception:
            pass  # UI can still load and surface DB errors gracefully
    
    yield
    
    # Shutdown
    try:
        close_pool()
    except Exception:
        pass


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="Ruko Admin Dashboard",
        description="Admin dashboard for monitoring Ruko chatbot analytics",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router)

    # Dashboard routes
    @app.get("/", include_in_schema=False)
    async def root():
        """Redirect root to dashboard."""
        return RedirectResponse(url="/dashboard")

    @app.get("/dashboard", include_in_schema=False)
    async def dashboard():
        """Serve the dashboard HTML."""
        static_path = Path(__file__).parent.parent / "frontend" / "dashboard.html"
        if not static_path.exists():
            return {"error": "Dashboard file not found", "path": str(static_path)}
        return FileResponse(str(static_path), media_type="text/html")

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(app, host="0.0.0.0", port=settings.app.port)
