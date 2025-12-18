"""
Admin Dashboard Service

Standalone FastAPI application for the RÜKO Admin Dashboard.
Provides a web UI and REST API for monitoring chatbot analytics.
"""
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add backend to path when running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from dotenv import load_dotenv
    load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse

# Use try/except for imports to support both module and script execution
try:
    from .config import get_settings
    from .database import close_pool, init_pool
    from .routes import api_router
except ImportError:
    from backend.config import get_settings
    from backend.database import close_pool, init_pool
    from backend.routes import api_router


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
        title="RÜKO Admin Dashboard",
        description="Admin dashboard for monitoring RÜKO chatbot analytics",
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
        """Serve the React frontend (production) or redirect to dev server."""
        # Check for built frontend first
        static_path = Path(__file__).parent.parent / "frontend" / "dist" / "index.html"
        if static_path.exists():
            return FileResponse(str(static_path), media_type="text/html")
        
        # Development mode - redirect to Vite dev server
        return {"message": "Run 'npm run dev' in frontend/ folder", "dev_url": "http://localhost:3000"}

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    port = int(os.getenv("PORT", "8080"))
    print(f"Starting backend on http://localhost:{port}")
    print("For frontend, run: cd frontend && npm run dev")
    uvicorn.run(app, host="0.0.0.0", port=port)
