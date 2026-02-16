from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.schemas import AddToCartRequest, CartOut, CheckoutResponse
from app.services.wordpress.cart_service import CartService
from app.services.wordpress.repository import WordPressRepository

router = APIRouter(prefix='/cart', tags=['cart'])


@router.post('/add-item', response_model=CartOut)
async def add_item(payload: AddToCartRequest, db: AsyncSession = Depends(get_db_session)) -> CartOut:
    repo = WordPressRepository(db)
    service = CartService(db, repo)
    cart = await service.add_item(payload.session_id, payload.product_id, payload.quantity)
    return CartOut(**cart)


@router.get('/{session_id}', response_model=CartOut)
async def get_cart(session_id: str, db: AsyncSession = Depends(get_db_session)) -> CartOut:
    repo = WordPressRepository(db)
    service = CartService(db, repo)
    cart = await service.get_cart(session_id)
    return CartOut(**cart)


@router.post('/{session_id}/checkout', response_model=CheckoutResponse)
async def checkout(session_id: str, db: AsyncSession = Depends(get_db_session)) -> CheckoutResponse:
    repo = WordPressRepository(db)
    service = CartService(db, repo)
    data = await service.checkout(session_id)
    return CheckoutResponse(**data)
