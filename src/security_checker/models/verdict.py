"""ReviewVerdict — 1 つの LLM の判定 (設計書 §6.2).

P1 時点では生成する経路がまだない (P2 の Reviewer が埋める) が、
LLM に強制する JSON スキーマとして先に固定する。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from security_checker.models.enums import Confidence, Verdict


class Usage(BaseModel):
    model_config = ConfigDict(frozen=True)

    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cached_tokens: int = 0
    estimated_usd: float | None = None
    cost_known: bool = True

    @property
    def total_tokens(self) -> int:
        """入力トークンと出力トークンの合計."""
        return self.input_tokens + self.output_tokens

    def merge(self, other: Usage) -> Usage:
        """複数呼び出しの合算. コストは片方でも不明なら不明として扱う."""
        known = self.cost_known and other.cost_known
        usd: float | None = None
        if known and (self.estimated_usd is not None or other.estimated_usd is not None):
            usd = (self.estimated_usd or 0.0) + (other.estimated_usd or 0.0)
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
            cached_tokens=self.cached_tokens + other.cached_tokens,
            estimated_usd=usd,
            cost_known=known,
        )


class ReviewVerdict(BaseModel):
    model_config = ConfigDict(frozen=True)

    reviewer: str
    verdict: Verdict
    confidence: Confidence = Confidence.MEDIUM
    reason: str = ""
    usage: Usage = Field(default_factory=Usage)
