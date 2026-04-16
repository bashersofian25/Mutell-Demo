from app.ai_engine.adapters.base import AIProviderAdapter
from app.ai_engine.adapters.anthropic import AnthropicAdapter
from app.ai_engine.adapters.deepseek import DeepseekAdapter
from app.ai_engine.adapters.gemini import GeminiAdapter
from app.ai_engine.adapters.openai import OpenAIAdapter
from app.ai_engine.adapters.zai import ZaiAdapter

_ADAPTERS: dict[str, type[AIProviderAdapter]] = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "gemini": GeminiAdapter,
    "zai": ZaiAdapter,
    "deepseek": DeepseekAdapter,
}


def get_adapter(provider_slug: str) -> AIProviderAdapter:
    adapter_cls = _ADAPTERS.get(provider_slug)
    if adapter_cls is None:
        raise ValueError(f"Unknown AI provider: {provider_slug}")
    return adapter_cls()
