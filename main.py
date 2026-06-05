from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from app.api.api import api_router
from app.api.web import router as web_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add Session Middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

app.include_router(web_router, tags=["web"])
app.include_router(api_router, prefix=settings.API_V1_STR)
