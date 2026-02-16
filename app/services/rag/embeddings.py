from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import Settings, get_settings


class EmbeddingService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        provider = self.settings.embedding_provider.lower()
        if provider != 'google':
            raise ValueError(f'Unsupported embedding provider: {self.settings.embedding_provider}')
        if not self.settings.gemini_api_key:
            raise ValueError('GEMINI_API_KEY is required for EMBEDDING_PROVIDER=google')
        self.client = GoogleGenerativeAIEmbeddings(
            model=self.settings.google_embedding_model,
            google_api_key=self.settings.gemini_api_key,
        )

    def embed_query(self, text: str) -> list[float]:
        return self.client.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.client.embed_documents(texts)
