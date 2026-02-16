from textwrap import dedent
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from app.services.llm.providers import LLMProviderFactory
from app.services.rag.retriever import ProductRAGService
from app.services.wordpress.cart_service import CartService
from app.services.wordpress.repository import WordPressRepository


SYSTEM_PROMPT = dedent(
    """
    You are a sales and support AI agent for an e-commerce store.

    Responsibilities:
    1) Answer customer questions about products using provided tool results.
    2) Clearly state availability and stock counts when present.
    3) Help users make purchase decisions and guide them to checkout.
    4) If user requests add-to-cart, call the add_to_cart tool with product_id and quantity.
    5) Use list_products for catalog requests and search_products for product Q&A.

    Rules:
    - Never invent stock data.
    - If retrieved products exist, mention product names explicitly in the final answer.
    - If context is insufficient, ask a short clarifying question.
    - Keep answers concise and actionable.
    """
).strip()


_HISTORY_STORE: dict[str, list] = {}


class CustomerAgent:
    def __init__(self, repo: WordPressRepository, cart_service: CartService):
        self.repo = repo
        self.cart_service = cart_service
        self.rag = ProductRAGService(repo)
        self.llm = LLMProviderFactory.create()
        self._used_products: list[int] = []
        self._product_names: list[str] = []
        self._session_id: str | None = None
        self._tools = self._build_tools()
        self._agent = create_react_agent(self.llm, self._tools)
        self._history_limit = 10

    def _reset_run_state(self, session_id: str) -> None:
        self._session_id = session_id
        self._used_products = []
        self._product_names = []

    def _get_history(self, session_id: str) -> list:
        return _HISTORY_STORE.get(session_id, []).copy()

    def _append_history(self, session_id: str, user_message: str, assistant_message: str) -> None:
        history = _HISTORY_STORE.get(session_id, [])
        history.append(HumanMessage(content=user_message))
        history.append(AIMessage(content=assistant_message))
        if len(history) > self._history_limit * 2:
            history = history[-self._history_limit * 2 :]
        _HISTORY_STORE[session_id] = history

    def _build_tools(self):
        @tool
        async def list_products(limit: int = 20) -> dict[str, Any]:
            """List available products with pricing and stock info."""
            products = await self.repo.list_products(limit=limit, offset=0)
            if not products:
                return {'summary': 'فعلا محصولی در فروشگاه ثبت نشده است.', 'products': []}

            lines: list[str] = []
            for idx, product in enumerate(products, start=1):
                name = str(product.get('name') or f'Product {idx}')
                price = product.get('price')
                stock_status = str(product.get('stock_status') or 'unknown')
                stock_quantity = product.get('stock_quantity')
                pid = product.get('id')
                if pid is not None and int(pid) not in self._used_products:
                    self._used_products.append(int(pid))
                if name not in self._product_names:
                    self._product_names.append(name)
                price_text = f'{price}' if price is not None else 'نامشخص'
                qty_text = f'{stock_quantity}' if stock_quantity is not None else 'نامشخص'
                lines.append(f'{idx}. {name} | قیمت: {price_text} | موجودی: {qty_text} | وضعیت: {stock_status}')

            summary = f'الان {len(products)} محصول در فروشگاه دارم:\n' + '\n'.join(lines)
            summary += '\nاگر بخواهی، روی هر کدام جزئیات کامل توضیح می‌دهم.'
            return {'summary': summary, 'products': products}

        @tool
        async def search_products(query: str, limit: int = 5) -> dict[str, Any]:
            """Retrieve relevant products for a user query and return RAG context."""
            rag_context, used_products, product_names = await self.rag.context_for_query(
                query,
                limit=limit,
            )
            self._used_products.extend([int(pid) for pid in used_products if pid not in self._used_products])
            for name in product_names:
                if name not in self._product_names:
                    self._product_names.append(name)
            return {
                'rag_context': rag_context,
                'product_names': product_names,
                'product_ids': used_products,
            }

        @tool
        async def add_to_cart(product_id: int, quantity: int = 1) -> dict[str, Any]:
            """Add a product to the cart and return checkout info."""
            if not self._session_id:
                raise ValueError('session_id is not set')
            qty = max(int(quantity), 1)
            cart = await self.cart_service.add_item(self._session_id, int(product_id), qty)
            checkout = await self.cart_service.checkout(self._session_id)
            if int(product_id) not in self._used_products:
                self._used_products.append(int(product_id))
            return {
                'product_id': int(product_id),
                'quantity': qty,
                'cart_total': cart.get('total'),
                'payment_url': checkout.get('payment_url'),
            }

        return [list_products, search_products, add_to_cart]

    async def run(self, session_id: str, user_message: str) -> dict[str, Any]:
        self._reset_run_state(session_id)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT + '\n\nRespond in Persian unless user asks otherwise.'),
        ]
        messages.extend(self._get_history(session_id))
        messages.append(HumanMessage(content=user_message))
        final_state = await self._agent.ainvoke({'messages': messages})
        message_list = final_state.get('messages') or []
        answer = str(message_list[-1].content) if message_list else ''

        if self._product_names and not any(name in answer for name in self._product_names):
            names_line = '، '.join(self._product_names)
            answer = f'محصولات پیدا شده: {names_line}\n{answer}'

        self._append_history(session_id, user_message, answer)

        return {
            'answer': answer,
            'session_id': session_id,
            'used_products': list(self._used_products),
        }
