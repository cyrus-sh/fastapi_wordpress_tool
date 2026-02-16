import re
from typing import Any

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings


class WordPressRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.t = self.settings.wp_table_prefix

    async def list_products(self, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        sql = text(
            f"""
            SELECT p.ID AS id,
                   p.post_title AS name,
                   p.post_content AS description,
                   CAST(pm_price.meta_value AS DECIMAL(12,2)) AS price,
                   CAST(pm_stock.meta_value AS SIGNED) AS stock_quantity,
                   pm_stock_status.meta_value AS stock_status
            FROM {self.t}posts p
            LEFT JOIN {self.t}postmeta pm_price
              ON pm_price.post_id = p.ID AND pm_price.meta_key = '_price'
            LEFT JOIN {self.t}postmeta pm_stock
              ON pm_stock.post_id = p.ID AND pm_stock.meta_key = '_stock'
            LEFT JOIN {self.t}postmeta pm_stock_status
              ON pm_stock_status.post_id = p.ID AND pm_stock_status.meta_key = '_stock_status'
            WHERE p.post_type = 'product' AND p.post_status = 'publish'
            ORDER BY p.post_date DESC
            LIMIT :limit OFFSET :offset
            """
        )
        result = await self.db.execute(sql, {'limit': limit, 'offset': offset})
        return [dict(row._mapping) for row in result.fetchall()]

    async def get_product(self, product_id: int) -> dict[str, Any]:
        sql = text(
            f"""
            SELECT p.ID AS id,
                   p.post_title AS name,
                   p.post_content AS description,
                   CAST(pm_price.meta_value AS DECIMAL(12,2)) AS price,
                   CAST(pm_stock.meta_value AS SIGNED) AS stock_quantity,
                   pm_stock_status.meta_value AS stock_status
            FROM {self.t}posts p
            LEFT JOIN {self.t}postmeta pm_price
              ON pm_price.post_id = p.ID AND pm_price.meta_key = '_price'
            LEFT JOIN {self.t}postmeta pm_stock
              ON pm_stock.post_id = p.ID AND pm_stock.meta_key = '_stock'
            LEFT JOIN {self.t}postmeta pm_stock_status
              ON pm_stock_status.post_id = p.ID AND pm_stock_status.meta_key = '_stock_status'
            WHERE p.post_type = 'product' AND p.ID = :product_id
            LIMIT 1
            """
        )
        row = (await self.db.execute(sql, {'product_id': product_id})).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='Product not found')
        return dict(row._mapping)

    async def search_products(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        normalized = (query or '').strip()
        if not normalized:
            return []

        phrase_results = await self._search_by_full_phrase(normalized, limit=limit)
        if phrase_results:
            return phrase_results

        tokens = self._extract_search_tokens(normalized)
        if not tokens:
            return []
        return await self._search_by_tokens(tokens=tokens, limit=limit)

    async def _search_by_full_phrase(self, query: str, limit: int) -> list[dict[str, Any]]:
        sql = text(
            f"""
            SELECT p.ID AS id,
                   p.post_title AS name,
                   p.post_content AS description,
                   CAST(pm_price.meta_value AS DECIMAL(12,2)) AS price,
                   CAST(pm_stock.meta_value AS SIGNED) AS stock_quantity,
                   pm_stock_status.meta_value AS stock_status
            FROM {self.t}posts p
            LEFT JOIN {self.t}postmeta pm_price
              ON pm_price.post_id = p.ID AND pm_price.meta_key = '_price'
            LEFT JOIN {self.t}postmeta pm_stock
              ON pm_stock.post_id = p.ID AND pm_stock.meta_key = '_stock'
            LEFT JOIN {self.t}postmeta pm_stock_status
              ON pm_stock_status.post_id = p.ID AND pm_stock_status.meta_key = '_stock_status'
            WHERE p.post_type = 'product'
              AND p.post_status = 'publish'
              AND (LOWER(p.post_title) LIKE :q OR LOWER(p.post_content) LIKE :q)
            ORDER BY p.post_date DESC
            LIMIT :limit
            """
        )
        result = await self.db.execute(sql, {'q': f'%{query.lower()}%', 'limit': limit})
        return [dict(row._mapping) for row in result.fetchall()]

    @staticmethod
    def _extract_search_tokens(query: str) -> list[str]:
        raw_tokens = re.findall(r'[0-9A-Za-z\u0600-\u06FF]+', query.lower())
        stop_words = {
            'a',
            'an',
            'and',
            'check',
            'database',
            'hello',
            'i',
            'in',
            'is',
            'me',
            'my',
            'name',
            'on',
            'please',
            'tell',
            'the',
            'to',
            'want',
            'دیتابیس',
            'سلام',
            'من',
            'میخوام',
            'میخواهم',
            'لطفا',
            'لطفاً',
            'و',
            'که',
            'از',
            'در',
            'رو',
            'را',
        }
        synonyms: dict[str, list[str]] = {
            'shoe': ['shoes', 'sneaker', 'sneakers', 'boot', 'boots', 'sandal', 'sandals', 'کفش', 'کتونی', 'بوت', 'صندل'],
            'shoes': ['shoe', 'sneaker', 'sneakers', 'boot', 'boots', 'sandal', 'sandals', 'کفش', 'کتونی', 'بوت', 'صندل'],
            'sneaker': ['shoe', 'shoes', 'sneakers', 'کفش', 'کتونی'],
            'sneakers': ['shoe', 'shoes', 'sneaker', 'کفش', 'کتونی'],
            'کفش': ['shoe', 'shoes', 'sneaker', 'sneakers', 'کتونی', 'بوت', 'صندل'],
            'کتونی': ['shoe', 'shoes', 'sneaker', 'sneakers', 'کفش'],
            'بوت': ['boot', 'boots', 'shoe', 'shoes', 'کفش'],
            'صندل': ['sandal', 'sandals', 'shoe', 'shoes', 'کفش'],
        }

        cleaned = [token for token in raw_tokens if token not in stop_words and (len(token) >= 3 or token.isdigit())]
        expanded: list[str] = []
        for token in cleaned:
            expanded.append(token)
            expanded.extend(synonyms.get(token, []))

        deduped: list[str] = []
        seen: set[str] = set()
        for token in expanded:
            if token in seen:
                continue
            seen.add(token)
            deduped.append(token)
        return deduped[:12]

    async def _search_by_tokens(self, tokens: list[str], limit: int) -> list[dict[str, Any]]:
        params: dict[str, Any] = {'limit': limit}
        like_conditions: list[str] = []
        score_parts: list[str] = []
        for idx, token in enumerate(tokens):
            key = f't{idx}'
            params[key] = f'%{token}%'
            like_conditions.append(f'(LOWER(p.post_title) LIKE :{key} OR LOWER(p.post_content) LIKE :{key})')
            score_parts.append(f'(CASE WHEN LOWER(p.post_title) LIKE :{key} THEN 2 ELSE 0 END)')
            score_parts.append(f'(CASE WHEN LOWER(p.post_content) LIKE :{key} THEN 1 ELSE 0 END)')

        where_sql = ' OR '.join(like_conditions)
        score_sql = ' + '.join(score_parts)
        sql = text(
            f"""
            SELECT p.ID AS id,
                   p.post_title AS name,
                   p.post_content AS description,
                   CAST(pm_price.meta_value AS DECIMAL(12,2)) AS price,
                   CAST(pm_stock.meta_value AS SIGNED) AS stock_quantity,
                   pm_stock_status.meta_value AS stock_status,
                   ({score_sql}) AS match_score
            FROM {self.t}posts p
            LEFT JOIN {self.t}postmeta pm_price
              ON pm_price.post_id = p.ID AND pm_price.meta_key = '_price'
            LEFT JOIN {self.t}postmeta pm_stock
              ON pm_stock.post_id = p.ID AND pm_stock.meta_key = '_stock'
            LEFT JOIN {self.t}postmeta pm_stock_status
              ON pm_stock_status.post_id = p.ID AND pm_stock_status.meta_key = '_stock_status'
            WHERE p.post_type = 'product'
              AND p.post_status = 'publish'
              AND ({where_sql})
            ORDER BY match_score DESC, p.post_date DESC
            LIMIT :limit
            """
        )
        rows = (await self.db.execute(sql, params)).fetchall()
        return [
            {k: v for k, v in dict(row._mapping).items() if k != 'match_score'}
            for row in rows
        ]

    async def ensure_agent_cart_tables(self) -> None:
        create_cart_sql = text(
            f"""
            CREATE TABLE IF NOT EXISTS {self.t}ai_agent_carts (
              id BIGINT AUTO_INCREMENT PRIMARY KEY,
              session_id VARCHAR(128) NOT NULL UNIQUE,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        create_items_sql = text(
            f"""
            CREATE TABLE IF NOT EXISTS {self.t}ai_agent_cart_items (
              id BIGINT AUTO_INCREMENT PRIMARY KEY,
              cart_id BIGINT NOT NULL,
              product_id BIGINT NOT NULL,
              quantity INT NOT NULL,
              unit_price DECIMAL(12,2) NULL,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              UNIQUE KEY uniq_cart_product (cart_id, product_id),
              CONSTRAINT fk_ai_cart FOREIGN KEY (cart_id)
                REFERENCES {self.t}ai_agent_carts(id)
                ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        await self.db.execute(create_cart_sql)
        await self.db.execute(create_items_sql)
        await self.db.commit()
