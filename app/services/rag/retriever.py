import asyncio
import math
import re
from typing import Any

from app.core.config import get_settings
from app.services.rag.embeddings import EmbeddingService
from app.services.wordpress.repository import WordPressRepository


class ProductRAGService:
    def __init__(self, repo: WordPressRepository):
        self.repo = repo
        self.settings = get_settings()
        self.embedding_service: EmbeddingService | None = None
        if self.settings.embedding_provider.lower() == 'google':
            self.embedding_service = EmbeddingService(self.settings)

    async def retrieve(self, user_query: str, limit: int = 5) -> list[dict[str, Any]]:
        if self._is_catalog_query(user_query):
            catalog_limit = max(limit, 20)
            return await self.repo.list_products(limit=catalog_limit, offset=0)

        semantic_results: list[dict[str, Any]] = []
        if self.embedding_service:
            try:
                semantic_results = await self._semantic_retrieve(user_query=user_query, limit=limit)
            except Exception:
                # Safe fallback to keyword search if embedding path fails.
                pass

        keyword_results = await self.repo.search_products(user_query, limit=limit)
        if not semantic_results:
            return keyword_results
        if not keyword_results:
            return semantic_results

        merged: list[dict[str, Any]] = []
        seen_ids: set[int] = set()
        for item in keyword_results + semantic_results:
            item_id = item.get('id')
            if item_id is None or item_id in seen_ids:
                continue
            seen_ids.add(int(item_id))
            merged.append(item)
            if len(merged) >= limit:
                break
        return merged

    @staticmethod
    def _is_catalog_query(user_query: str) -> bool:
        text = (user_query or '').strip().lower()
        if not text:
            return False

        patterns = [
            r'\bwhat products\b',
            r'\ball products\b',
            r'\bproducts do you have\b',
            r'\bshow (me )?(all )?products\b',
            r'\bproduct list\b',
            r'چه محصول',
            r'چه کالا',
            r'چه چیز',
            r'همه محصولات',
            r'لیست محصولات',
            r'کلا چی داری',
            r'چی داری',
            r'چه داری',
        ]
        return any(re.search(pattern, text) for pattern in patterns)

    @staticmethod
    def _product_to_text(product: dict[str, Any]) -> str:
        return (
            f"ID: {product.get('id')}\n"
            f"Name: {product.get('name')}\n"
            f"Description: {product.get('description')}\n"
            f"Price: {product.get('price')}\n"
            f"Stock Quantity: {product.get('stock_quantity')}\n"
            f"Stock Status: {product.get('stock_status')}"
        )

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return -1.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return -1.0
        return dot / (norm_a * norm_b)

    async def _semantic_retrieve(self, user_query: str, limit: int = 5) -> list[dict[str, Any]]:
        products = await self.repo.list_products(limit=max(limit * 20, 100), offset=0)
        if not products:
            return []

        texts = [self._product_to_text(p) for p in products]
        query_embedding = await asyncio.to_thread(self.embedding_service.embed_query, user_query)
        doc_embeddings = await asyncio.to_thread(self.embedding_service.embed_documents, texts)

        ranked: list[tuple[float, dict[str, Any]]] = []
        for product, embedding in zip(products, doc_embeddings):
            score = self._cosine_similarity(query_embedding, embedding)
            ranked.append((score, product))
        ranked.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in ranked[:limit]]

    @staticmethod
    def format_context(products: list[dict[str, Any]]) -> str:
        if not products:
            return 'No relevant products found.'

        chunks: list[str] = []
        for p in products:
            chunks.append(
                (
                    f"Product ID: {p.get('id')}\n"
                    f"Name: {p.get('name')}\n"
                    f"Price: {p.get('price')}\n"
                    f"Stock Quantity: {p.get('stock_quantity')}\n"
                    f"Stock Status: {p.get('stock_status')}\n"
                    f"Description: {str(p.get('description') or '')[:500]}"
                )
            )
        return '\n\n---\n\n'.join(chunks)

    async def context_for_query(self, user_query: str, limit: int = 5) -> tuple[str, list[int], list[str]]:
        products = await self.retrieve(user_query=user_query, limit=limit)
        return (
            self.format_context(products),
            [int(p['id']) for p in products if p.get('id') is not None],
            [str(p.get('name')) for p in products if p.get('name')],
        )
