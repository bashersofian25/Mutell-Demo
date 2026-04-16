from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json


@dataclass
class EvaluationResult:
    overall: float | None = None
    sentiment: float | None = None
    sentiment_label: str | None = None
    politeness: float | None = None
    compliance: float | None = None
    resolution: float | None = None
    upselling: float | None = None
    response_time: float | None = None
    honesty: float | None = None
    language_detected: str | None = None
    summary: str | None = None
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    unclear_items: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    unavailable_items: list[str] = field(default_factory=list)
    swearing_count: int = 0
    swearing_instances: list[str] = field(default_factory=list)
    off_topic_count: int = 0
    off_topic_segments: list[str] = field(default_factory=list)
    speaker_segments: list[dict] = field(default_factory=list)
    raw_response: dict = field(default_factory=dict)
    tokens_used: int | None = None
    duration_ms: int | None = None


class AIProviderAdapter(ABC):
    @abstractmethod
    async def evaluate(
        self,
        raw_text: str,
        system_prompt: str,
        user_prompt: str,
        model: str,
        api_key: str,
        base_url: str | None = None,
    ) -> EvaluationResult:
        ...

    def _parse_response(
        self, content: str, tokens_used: int | None, duration_ms: int, raw: dict, extract_json: bool = False
    ) -> EvaluationResult:
        parsed = None
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            if extract_json:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    try:
                        parsed = json.loads(content[json_start:json_end])
                    except json.JSONDecodeError:
                        pass

            if parsed is None:
                return EvaluationResult(
                    raw_response={"raw_content": content},
                    tokens_used=tokens_used,
                    duration_ms=duration_ms,
                )

        return EvaluationResult(
            overall=parsed.get("overall"),
            sentiment=parsed.get("sentiment"),
            sentiment_label=parsed.get("sentiment_label"),
            politeness=parsed.get("politeness"),
            compliance=parsed.get("compliance"),
            resolution=parsed.get("resolution"),
            upselling=parsed.get("upselling"),
            response_time=parsed.get("response_time"),
            honesty=parsed.get("honesty"),
            language_detected=parsed.get("language_detected"),
            summary=parsed.get("summary"),
            strengths=parsed.get("strengths", []),
            weaknesses=parsed.get("weaknesses", []),
            recommendations=parsed.get("recommendations", []),
            unclear_items=parsed.get("unclear_items", []),
            flags=parsed.get("flags", []),
            unavailable_items=parsed.get("unavailable_items", []),
            swearing_count=parsed.get("swearing_count", 0) or 0,
            swearing_instances=parsed.get("swearing_instances", []),
            off_topic_count=parsed.get("off_topic_count", 0) or 0,
            off_topic_segments=parsed.get("off_topic_segments", []),
            speaker_segments=parsed.get("speaker_segments", []),
            raw_response=raw,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
        )
