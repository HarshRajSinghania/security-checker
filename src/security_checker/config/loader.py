"""設定の探索・合成・検証 (設計書 §12).

合成順序 (後勝ち):
  組み込み既定値 ← preset ← 設定ファイル ← ローカル設定 ← 環境変数 ← CLI フラグ

「ローカル設定」は git 管理しない個人用の上書き層 (`security-checker.local.yml`)。
共有する設定と、手元でだけ使う Reviewer 定義を混ぜないためにある。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from security_checker.config.schema import Config, ReviewerConfig
from security_checker.errors import ConfigError

# 探索対象のファイル名
CONFIG_FILENAMES = (
    "security-checker.yml",
    "security-checker.yaml",
    ".security-checker.yml",
    ".security-checker.yaml",
)
LOCAL_CONFIG_FILENAMES = (
    "security-checker.local.yml",
    "security-checker.local.yaml",
)

PRESET_DIR = Path(__file__).parent.parent / "providers" / "presets"


@dataclass
class LoadedConfig:
    config: Config
    path: Path | None = None
    warnings: list[str] = field(default_factory=list)


def find_config(root: Path) -> Path | None:
    for name in CONFIG_FILENAMES:
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def find_local_config(root: Path) -> Path | None:
    for name in LOCAL_CONFIG_FILENAMES:
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def available_presets() -> list[str]:
    """同梱プリセットの名前一覧を返す."""
    return sorted(path.stem for path in PRESET_DIR.glob("*.yml"))


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} の YAML を解釈できません: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"{path} を読み込めません: {exc}") from exc
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} のトップレベルはマッピングである必要があります")
    return raw


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(current, value)
        else:
            merged[key] = value
    return merged


def load_config(
    root: Path,
    *,
    config_path: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> LoadedConfig:
    """設定を探索して合成し、検証済みの Config を返す.

    存在しないファイルはスキップする。ファイルが壊れていたら例外を上げる。
    """
    warnings: list[str] = []
    data: dict[str, Any] = {}

    # preset
    # (プリセットの適用は schema 側でやる。ここではファイルと CLI を合成する)

    path = config_path or find_config(root)
    if path is not None:
        data = _deep_merge(data, _read_yaml(path))

    local_path = find_local_config(root)
    if local_path is not None:
        data = _deep_merge(data, _read_yaml(local_path))

    # 環境変数による上書き
    # (実装は schema と cli 側に委譲)

    if cli_overrides:
        data = _deep_merge(data, cli_overrides)

    try:
        config = Config.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(f"設定の検証に失敗しました: {exc}") from exc

    return LoadedConfig(config=config, path=path, warnings=warnings)
