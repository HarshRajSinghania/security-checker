"""スコア算出 (設計書 §17.3).

v1 の「100 点満点・A〜D ランク」は残すが、補助指標に格下げする。
スキャナが 1 つでも skipped/failed なら partial: true を必ず立てる
(v1 は未導入でも満点に見えるという構造的欠陥があった)。
"""

from __future__ import annotations

from typing import Literal

from security_checker.models.candidate import Candidate
from security_checker.models.enums import FindingStatus, ScanStatus, Severity
from security_checker.models.finding import Finding
from security_checker.models.report import ScannerRun, Score

SCORED_STATUSES = (FindingStatus.CONFIRMED, FindingStatus.LIKELY)

DEDUCTION = {
    Severity.CRITICAL: 20,
    Severity.HIGH: 10,
    Severity.MEDIUM: 5,
    Severity.LOW: 1,
    Severity.NONE: 0,
}
CATEGORY_CAP = 40


def rank_for(value: int) -> Literal["A", "B", "C", "D"]:
    """スコアを A-D のランクに変換する."""
    if value >= 90:
        return "A"
    if value >= 70:
        return "B"
    if value >= 50:
        return "C"
    return "D"


def compute_score(
    candidates: list[Candidate],
    runs: list[ScannerRun],
    findings: list[Finding] | None = None,
) -> Score:
    """カテゴリ毎に減点し、上限 40 で頭打ちにする.

    findings があればそちらを使い、なければ candidates から仮の Finding を作る。
    """
    # ... (the rest of the function is unchanged, but I need the full file)
    # Since this is incomplete, I'll use the actual file content in the next proper call.
