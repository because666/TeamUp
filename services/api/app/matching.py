from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from types import MappingProxyType


ENGINE_TYPE = "RULE"
ENGINE_VERSION = "match-v0.1"
MINIMUM_CONFIDENCE = Decimal("0.60")
SAFE_EXCLUSION_REASONS = frozenset(
    {
        "CANDIDATE_NOT_ELIGIBLE",
        "TARGET_NOT_AVAILABLE",
        "REQUIRED_CONDITION_NOT_MET",
    }
)
FACTOR_WEIGHTS = MappingProxyType(
    {
        "skill": 35,
        "direction": 20,
        "availability": 20,
        "professional": 10,
        "experience": 10,
        "collaboration": 5,
    }
)


@dataclass(frozen=True)
class ConstraintResult:
    key: str
    passed: bool
    reason_code: str


@dataclass(frozen=True)
class MatchFeatures:
    target_id: str
    candidate_skills: tuple[str, ...] | None = None
    desired_skills: tuple[str, ...] | None = None
    required_skills: tuple[str, ...] = ()
    direction_score: float | int | Decimal | None = None
    candidate_hours_per_week: int | None = None
    required_hours_per_week: int | None = None
    professional_score: float | int | Decimal | None = None
    experience_score: float | int | Decimal | None = None
    collaboration_score: float | int | Decimal | None = None
    constraints: tuple[ConstraintResult, ...] = ()


@dataclass(frozen=True)
class MatchFactor:
    key: str
    score: int
    reason_code: str


@dataclass(frozen=True)
class MatchDecision:
    target_id: str
    eligible: bool
    score: int
    confidence: float
    ranking_score: float
    engine_type: str
    engine_version: str
    model_version: None
    factors: tuple[MatchFactor, ...]
    missing_information: tuple[str, ...]
    information_sufficient: bool
    exclusion_reasons: tuple[str, ...]


def score_match(features: MatchFeatures) -> MatchDecision:
    if not features.target_id.strip():
        raise ValueError("target_id must not be empty")
    invalid_reasons = {
        constraint.reason_code
        for constraint in features.constraints
        if constraint.reason_code not in SAFE_EXCLUSION_REASONS
    }
    if invalid_reasons:
        raise ValueError("constraint reason_code must be a safe public code")
    exclusions = [constraint.reason_code for constraint in features.constraints if not constraint.passed]
    required_exclusion = _required_skill_exclusion(features)
    if required_exclusion:
        exclusions.append(required_exclusion)
    if exclusions:
        return MatchDecision(
            target_id=features.target_id,
            eligible=False,
            score=0,
            confidence=0.0,
            ranking_score=0.0,
            engine_type=ENGINE_TYPE,
            engine_version=ENGINE_VERSION,
            model_version=None,
            factors=(),
            missing_information=(),
            information_sufficient=False,
            exclusion_reasons=tuple(sorted(set(exclusions))),
        )

    factor_scores = {
        "skill": _skill_score(features.candidate_skills, features.desired_skills, features.required_skills),
        "direction": _optional_score(features.direction_score, "direction_score"),
        "availability": _availability_score(
            features.candidate_hours_per_week,
            features.required_hours_per_week,
        ),
        "professional": _optional_score(features.professional_score, "professional_score"),
        "experience": _optional_score(features.experience_score, "experience_score"),
        "collaboration": _optional_score(features.collaboration_score, "collaboration_score"),
    }
    factors = tuple(
        MatchFactor(key=key, score=_round_integer(value), reason_code=_reason_code(key, value))
        for key, value in factor_scores.items()
        if value is not None
    )
    missing = tuple(key for key, value in factor_scores.items() if value is None)
    available_weight = sum(FACTOR_WEIGHTS[factor.key] for factor in factors)
    confidence = Decimal(available_weight) / Decimal(100)
    if not factors:
        raw_score = Decimal(0)
    else:
        weighted_total = sum(
            Decimal(FACTOR_WEIGHTS[factor.key]) * factor_scores[factor.key]
            for factor in factors
        )
        raw_score = weighted_total / Decimal(available_weight)
    ranking_score = raw_score * (Decimal("0.7") + Decimal("0.3") * confidence)

    return MatchDecision(
        target_id=features.target_id,
        eligible=True,
        score=_round_integer(raw_score),
        confidence=_round_decimal(confidence),
        ranking_score=_round_decimal(ranking_score),
        engine_type=ENGINE_TYPE,
        engine_version=ENGINE_VERSION,
        model_version=None,
        factors=factors,
        missing_information=missing,
        information_sufficient=confidence >= MINIMUM_CONFIDENCE,
        exclusion_reasons=(),
    )


def _required_skill_exclusion(features: MatchFeatures) -> str | None:
    required = _normalized_skills(features.required_skills)
    if not required:
        return None
    if features.candidate_skills is None:
        return "REQUIRED_SKILL_UNVERIFIED"
    candidate = _normalized_skills(features.candidate_skills)
    if not required.issubset(candidate):
        return "REQUIRED_SKILL_NOT_MET"
    return None


def _skill_score(
    candidate_skills: tuple[str, ...] | None,
    desired_skills: tuple[str, ...] | None,
    required_skills: tuple[str, ...],
) -> Decimal | None:
    if candidate_skills is None:
        return None
    target = _normalized_skills(required_skills)
    if desired_skills is not None:
        target |= _normalized_skills(desired_skills)
    if not target:
        return None
    candidate = _normalized_skills(candidate_skills)
    overlap = len(candidate & target)
    return Decimal(overlap * 100) / Decimal(len(target))


def _availability_score(candidate_hours: int | None, required_hours: int | None) -> Decimal | None:
    if candidate_hours is None or required_hours is None:
        return None
    if candidate_hours < 0:
        raise ValueError("candidate_hours_per_week must be non-negative")
    if required_hours <= 0:
        raise ValueError("required_hours_per_week must be positive")
    return min(Decimal(candidate_hours) / Decimal(required_hours), Decimal(1)) * Decimal(100)


def _optional_score(value: float | int | Decimal | None, field_name: str) -> Decimal | None:
    if value is None:
        return None
    score = Decimal(str(value))
    if not Decimal(0) <= score <= Decimal(100):
        raise ValueError(f"{field_name} must be between 0 and 100")
    return score


def _normalized_skills(values: tuple[str, ...]) -> set[str]:
    return {value.strip().casefold() for value in values if value.strip()}


def _reason_code(key: str, score: Decimal) -> str:
    prefixes = {
        "skill": "SKILL_OVERLAP",
        "direction": "DIRECTION_ALIGNMENT",
        "availability": "AVAILABILITY",
        "professional": "PROFESSIONAL_RELEVANCE",
        "experience": "EXPERIENCE_RELEVANCE",
        "collaboration": "COLLABORATION_PREFERENCE",
    }
    level = "HIGH" if score >= 80 else "PARTIAL" if score >= 50 else "LOW"
    return f"{prefixes[key]}_{level}"


def _round_integer(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _round_decimal(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
