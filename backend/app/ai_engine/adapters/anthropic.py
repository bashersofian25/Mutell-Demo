import time

import httpx

from app.ai_engine.adapters.base import AIProviderAdapter, EvaluationResult


class AnthropicAdapter(AIProviderAdapter):
    async def evaluate(
        self,
        raw_text: str,
        system_prompt: str,
        user_prompt: str,
        model: str,
        api_key: str,
    ) -> EvaluationResult:
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 2048,
                    "system": system_prompt,
                    "messages": [
                        {"role": "user", "content": user_prompt},
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()

        duration_ms = round((time.monotonic() - start) * 1000)
        content = data["content"][0]["text"]
        tokens_used = data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)

        return self._parse_response(content, tokens_used, duration_ms, data, extract_json=True)
