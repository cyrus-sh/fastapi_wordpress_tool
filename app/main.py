from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.routers import cart, chat, health, products

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.include_router(health.router, prefix='/api/v1')
app.include_router(products.router, prefix='/api/v1')
app.include_router(cart.router, prefix='/api/v1')
app.include_router(chat.router, prefix='/api/v1')


@app.get('/')
async def root() -> dict[str, str]:
    return {'message': settings.app_name, 'docs': '/docs'}
