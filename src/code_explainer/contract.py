from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


Confidence = Literal["high", "medium", "low"]


@dataclass
class InputInfo:
    name: str
    role: str
    default: str | None = None


@dataclass
class OutputInfo:
    kind: str
    description: str


@dataclass
class BugInfo:
    risk: str
    evidence: str
    suggestion: str


@dataclass
class TestSuggestion:
    case: str
    reason: str


@dataclass
class CodeExplanation:
    function_name: str
    summary: str
    inputs: list[InputInfo] = field(default_factory=list)
    outputs: list[OutputInfo] = field(default_factory=list)
    potential_bugs: list[BugInfo] = field(default_factory=list)
    test_suggestions: list[TestSuggestion] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    confidence: Confidence = "medium"

    def to_dict(self) -> dict:
        return asdict(self)
