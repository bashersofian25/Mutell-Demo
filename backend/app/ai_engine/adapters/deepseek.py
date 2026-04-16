import time

import httpx

from app.ai_engine.adapters.base import AIProviderAdapter, EvaluationResult


class DeepseekAdapter(AIProviderAdapter):
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
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            data = response.json()

        duration_ms = round((time.monotonic() - start) * 1000)
        content = data["choices"][0]["message"]["content"]
        tokens_used = data.get("usage", {}).get("total_tokens")

        return self._parse_response(content, tokens_used, duration_ms, data)
