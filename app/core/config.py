from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = Field(default='AI Sales Agent API', alias='APP_NAME')
    app_env: str = Field(default='dev', alias='APP_ENV')
    app_host: str = Field(default='0.0.0.0', alias='APP_HOST')
    app_port: int = Field(default=8000, alias='APP_PORT')
    debug: bool = Field(default=True, alias='DEBUG')

    mysql_host: str = Field(default='localhost', alias='MYSQL_HOST')
    mysql_port: int = Field(default=3306, alias='MYSQL_PORT')
    mysql_user: str = Field(default='wpuser', alias='MYSQL_USER')
    mysql_password: str = Field(default='password', alias='MYSQL_PASSWORD')
    mysql_db: str = Field(default='wordpress', alias='MYSQL_DB')
    wp_table_prefix: str = Field(default='wp_', alias='WP_TABLE_PREFIX')

    llm_provider: str = Field(default='gemini', alias='LLM_PROVIDER')
    llm_model: str = Field(default='gemini-1.5-flash', alias='LLM_MODEL')
    llm_temperature: float = Field(default=0.2, alias='LLM_TEMPERATURE')
    gemini_model: str = Field(default='gemini-1.5-flash', alias='GEMINI_MODEL')

    openai_api_key: str | None = Field(default=None, alias='OPENAI_API_KEY')
    gemini_api_key: str | None = Field(default=None, alias='GEMINI_API_KEY')
    deepseek_api_key: str | None = Field(default=None, alias='DEEPSEEK_API_KEY')
    deepseek_base_url: str = Field(default='https://api.deepseek.com', alias='DEEPSEEK_BASE_URL')

    openai_compatible_base_url: str | None = Field(default=None, alias='OPENAI_COMPATIBLE_BASE_URL')
    openai_compatible_api_key: str | None = Field(default=None, alias='OPENAI_COMPATIBLE_API_KEY')

    embedding_provider: str = Field(default='keyword', alias='EMBEDDING_PROVIDER')
    google_embedding_model: str = Field(default='models/text-embedding-004', alias='GOOGLE_EMBEDDING_MODEL')
    openai_embeddings_model: str | None = Field(default=None, alias='OPENAI_EMBEDDINGS_MODEL')

    wp_checkout_base_url: str = Field(default='https://example.com/checkout', alias='WP_CHECKOUT_BASE_URL')

    @property
    def mysql_async_dsn(self) -> str:
        # URL-encode credentials/db so special characters in .env don't break auth.
        user = quote_plus(self.mysql_user)
        password = quote_plus(self.mysql_password)
        db = quote_plus(self.mysql_db)
        return f"mysql+aiomysql://{user}:{password}@{self.mysql_host}:{self.mysql_port}/{db}?charset=utf8mb4"


@lru_cache
def get_settings() -> Settings:
    return Settings()
