from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import Settings, get_settings


class LLMProviderFactory:
    @staticmethod
    def _effective_gemini_model(cfg: Settings) -> str:
        model = (cfg.gemini_model or '').strip() or (cfg.llm_model or '').strip()
        if not model:
            raise ValueError('Set GEMINI_MODEL (or LLM_MODEL) for provider=gemini')
        if model.startswith('models/'):
            return model.removeprefix('models/')
        return model

    @staticmethod
    def create(settings: Settings | None = None) -> BaseChatModel:
        cfg = settings or get_settings()
        provider = cfg.llm_provider.lower().strip()

        # Gemini-only mode: route common/legacy provider names to Gemini.
        if provider in {
            'google',
            'google_ai_studio',
            'aistudio',
            'google_aistudio',
            'gemini',
            'openai',
            'deepseek',
            'openai_compatible',
        }:
            provider = 'gemini'

        if provider != 'gemini':
            raise ValueError(f'Unsupported LLM provider: {cfg.llm_provider}')

        if not cfg.gemini_api_key:
            raise ValueError('GEMINI_API_KEY is required for provider=gemini')

        model = LLMProviderFactory._effective_gemini_model(cfg)
        return ChatGoogleGenerativeAI(
            google_api_key=cfg.gemini_api_key,
            model=model,
            temperature=cfg.llm_temperature,
        )


def llm_metadata(settings: Settings | None = None) -> dict[str, Any]:
    cfg = settings or get_settings()
    return {
        'provider': 'gemini',
        'model': LLMProviderFactory._effective_gemini_model(cfg),
        'temperature': cfg.llm_temperature,
    }
