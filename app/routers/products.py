from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.schemas import ProductListResponse, ProductOut
from app.services.wordpress.repository import WordPressRepository

router = APIRouter(prefix='/products', tags=['products'])


@router.get('', response_model=ProductListResponse)
async def list_products(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db_session),
) -> ProductListResponse:
    repo = WordPressRepository(db)
    items = await repo.list_products(limit=limit, offset=offset)
    return ProductListResponse(items=[ProductOut(**item) for item in items])


@router.get('/{product_id}', response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db_session)) -> ProductOut:
    repo = WordPressRepository(db)
    product = await repo.get_product(product_id)
    return ProductOut(**product)
