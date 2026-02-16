from typing import Any
from urllib.parse import urlencode

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.services.wordpress.repository import WordPressRepository


class CartService:
    def __init__(self, db: AsyncSession, repo: WordPressRepository):
        self.db = db
        self.repo = repo
        self.settings = get_settings()

    async def _get_or_create_cart_id(self, session_id: str) -> int:
        await self.repo.ensure_agent_cart_tables()
        t = self.settings.wp_table_prefix

        select_sql = text(f"SELECT id FROM {t}ai_agent_carts WHERE session_id = :session_id LIMIT 1")
        row = (await self.db.execute(select_sql, {'session_id': session_id})).fetchone()
        if row:
            return int(row[0])

        insert_sql = text(f"INSERT INTO {t}ai_agent_carts(session_id) VALUES(:session_id)")
        await self.db.execute(insert_sql, {'session_id': session_id})
        await self.db.commit()
        row = (await self.db.execute(select_sql, {'session_id': session_id})).fetchone()
        if not row:
            raise HTTPException(status_code=500, detail='Failed to create cart')
        return int(row[0])

    async def add_item(self, session_id: str, product_id: int, quantity: int) -> dict[str, Any]:
        product = await self.repo.get_product(product_id)

        if product.get('stock_status') == 'outofstock' or (product.get('stock_quantity') is not None and int(product['stock_quantity']) <= 0):
            raise HTTPException(status_code=400, detail='Product is out of stock')

        cart_id = await self._get_or_create_cart_id(session_id)
        t = self.settings.wp_table_prefix

        upsert_sql = text(
            f"""
            INSERT INTO {t}ai_agent_cart_items (cart_id, product_id, quantity, unit_price)
            VALUES (:cart_id, :product_id, :quantity, :unit_price)
            ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity), unit_price = VALUES(unit_price)
            """
        )
        await self.db.execute(
            upsert_sql,
            {
                'cart_id': cart_id,
                'product_id': product_id,
                'quantity': quantity,
                'unit_price': product.get('price'),
            },
        )
        await self.db.commit()

        return await self.get_cart(session_id)

    async def get_cart(self, session_id: str) -> dict[str, Any]:
        t = self.settings.wp_table_prefix
        sql = text(
            f"""
            SELECT i.product_id, i.quantity, i.unit_price,
                   (i.quantity * COALESCE(i.unit_price, 0)) AS line_total
            FROM {t}ai_agent_carts c
            JOIN {t}ai_agent_cart_items i ON i.cart_id = c.id
            WHERE c.session_id = :session_id
            ORDER BY i.id ASC
            """
        )
        rows = (await self.db.execute(sql, {'session_id': session_id})).fetchall()
        items = [dict(r._mapping) for r in rows]
        total = float(sum(float(item.get('line_total') or 0) for item in items))
        return {'session_id': session_id, 'items': items, 'total': total}

    async def checkout(self, session_id: str) -> dict[str, Any]:
        cart = await self.get_cart(session_id)
        if not cart['items']:
            raise HTTPException(status_code=400, detail='Cart is empty')

        query = urlencode({'agent_session': session_id})
        payment_url = f"{self.settings.wp_checkout_base_url}?{query}"
        return {'session_id': session_id, 'payment_url': payment_url}
