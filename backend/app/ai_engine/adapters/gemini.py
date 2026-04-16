import time

import httpx

from app.ai_engine.adapters.base import AIProviderAdapter, EvaluationResult


class GeminiAdapter(AIProviderAdapter):
    async def evaluate(
        self,
        raw_text: str,
        system_prompt: str,
        user_prompt: str,
        model: str,
        api_key: str,
    ) -> EvaluationResult:
        start = time.monotonic()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                headers={
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "system_instruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"parts": [{"text": user_prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "responseMimeType": "application/json",
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

        duration_ms = round((time.monotonic() - start) * 1000)
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        tokens_used = data.get("usageMetadata", {}).get("totalTokenCount")

        return self._parse_response(content, tokens_used, duration_ms, data)
