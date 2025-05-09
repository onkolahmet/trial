"""
FastAPI application setup.
"""
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import uvicorn

from src.api.endpoints import router
from src.core.config import API_TITLE, API_DESCRIPTION, API_VERSION, HOST, PORT

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION
    )
    
    # Add root route to redirect to docs
    @app.get("/", include_in_schema=False)
    async def root():
        """Redirect to the API documentation."""
        return RedirectResponse(url="/docs")
    
    # Add routes
    app.include_router(router)
    
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("src.api.app:app", host=HOST, port=PORT, reload=True)
