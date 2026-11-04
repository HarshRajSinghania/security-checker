"""集約戦略の解決 (設計書 §13, §29)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from importlib.metadata import entry_points

from security_checker.aggregate.base import Aggregator
from security_checker.aggregate.consensus import ConsensusAggregator
from security_checker.aggregate.weighted import WeightedAggregator
from security_checker.errors import ConfigError

ENTRY_POINT_GROUP = "security_checker.aggregators"

# judge は LLM 呼び出しを伴うため、同期の Aggregator ではなく run.review_and_aggregate が扱う
# (fallback 戦略で集約したあと、割れた候補だけを Judge に回す。aggregate/judge.py)
BUILTIN_AGGREGATORS: dict[str, Callable[..., Aggregator]] = {
    ConsensusAggregator.name: ConsensusAggregator,
    WeightedAggregator.name: WeightedAggregator,
}


def discover_plugin_aggregators() -> tuple[dict[str, Callable[..., Aggregator]], list[str]]:
    """エントリーポイントからプラグイン Aggregator を発見する."""
    found: dict[str, Callable[..., Aggregator]] = {}
    warnings: list[str] = []
    for entry in entry_points(group=ENTRY_POINT_GROUP):
        try:
            found[entry.name] = entry.load()
        except Exception as exc:  # プラグイン側の任意の失敗を封じ込める
            warnings.append(f"aggregator プラグイン '{entry.name}' の読み込みに失敗しました: {exc}")
    return found, warnings


def build_aggregator(
    strategy: str, *, weights: Mapping[str, float] | None = None
) -> tuple[Aggregator, list[str]]:
    """戦略名から Aggregator を作る.

    `weights` は Reviewer 名 → 重み。**戦略ごとの分岐を作らない**ため、
    どの戦略にも同じものを渡し、使わない戦略は受け取って無視する
    (P1: 分岐を増やさない)。
    """
    warnings: list[str] = []
    plugins, plugin_warnings = discover_plugin_aggregators()
    warnings.extend(plugin_warnings)
    registry = {**BUILTIN_AGGREGATORS, **plugins}
    if strategy not in registry:
        available = ", ".join(sorted(registry))
        raise ConfigError(f"不明な集約戦略 '{strategy}' です (利用可能: {available})")
    return registry[strategy](weights=weights), warnings
