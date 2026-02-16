from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.schemas import ChatRequest, ChatResponse
from app.services.agent.customer_agent import CustomerAgent
from app.services.wordpress.cart_service import CartService
from app.services.wordpress.repository import WordPressRepository

router = APIRouter(prefix='/chat', tags=['chat'])


@router.post('/query', response_model=ChatResponse)
async def chat_query(payload: ChatRequest, db: AsyncSession = Depends(get_db_session)) -> ChatResponse:
    repo = WordPressRepository(db)
    cart_service = CartService(db, repo)
    agent = CustomerAgent(repo=repo, cart_service=cart_service)
    response = await agent.run(payload.session_id, payload.message)
    return ChatResponse(**response)
