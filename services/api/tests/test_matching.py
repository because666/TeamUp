import pytest

from app.matching import ConstraintResult, MatchFeatures, score_match


def test_confirmed_v01_weights_golden_case() -> None:
    result = score_match(
        MatchFeatures(
            target_id="target-golden",
            candidate_skills=("Python", "MySQL", "FastAPI"),
            desired_skills=("Python", "MySQL", "Vue", "FastAPI"),
            direction_score=100,
            candidate_hours_per_week=8,
            required_hours_per_week=10,
            professional_score=50,
            experience_score=100,
            collaboration_score=0,
        )
    )

    assert result.eligible is True
    assert result.score == 77
    assert result.confidence == 1.0
    assert result.ranking_score == 77.25
    assert result.engine_type == "RULE"
    assert result.engine_version == "match-v0.1"
    assert result.model_version is None
    assert [(factor.key, factor.score) for factor in result.factors] == [
        ("skill", 75),
        ("direction", 100),
        ("availability", 80),
        ("professional", 50),
        ("experience", 100),
        ("collaboration", 0),
    ]
    assert result.factors[0].reason_code == "SKILL_OVERLAP_PARTIAL"
    assert result.missing_information == ()
    assert result.information_sufficient is True


def test_missing_factors_are_renormalized_and_reduce_ranking_confidence() -> None:
    result = score_match(
        MatchFeatures(
            target_id="target-partial",
            candidate_skills=("Python", "MySQL"),
            desired_skills=("python", "MYSQL"),
            candidate_hours_per_week=4,
            required_hours_per_week=8,
        )
    )

    assert result.score == 82
    assert result.confidence == 0.55
    assert result.ranking_score == 70.7727
    assert result.missing_information == ("direction", "professional", "experience", "collaboration")
    assert result.information_sufficient is False


def test_required_skill_and_external_hard_constraints_exclude_candidate() -> None:
    missing_skill = score_match(
        MatchFeatures(
            target_id="candidate-a",
            candidate_skills=("Python",),
            desired_skills=("Python", "MySQL"),
            required_skills=("MySQL",),
        )
    )
    blocked = score_match(
        MatchFeatures(
            target_id="candidate-b",
            constraints=(ConstraintResult("block", False, "CANDIDATE_NOT_ELIGIBLE"),),
        )
    )

    assert missing_skill.eligible is False
    assert missing_skill.exclusion_reasons == ("REQUIRED_SKILL_NOT_MET",)
    assert blocked.eligible is False
    assert blocked.exclusion_reasons == ("CANDIDATE_NOT_ELIGIBLE",)
    assert blocked.score == 0


def test_unknown_required_skill_is_not_treated_as_satisfied() -> None:
    result = score_match(
        MatchFeatures(
            target_id="candidate-unknown",
            candidate_skills=None,
            desired_skills=("Python",),
            required_skills=("Python",),
        )
    )

    assert result.eligible is False
    assert result.exclusion_reasons == ("REQUIRED_SKILL_UNVERIFIED",)


def test_required_skills_alone_produce_a_skill_factor_when_satisfied() -> None:
    result = score_match(
        MatchFeatures(
            target_id="required-only",
            candidate_skills=("Python", "MySQL"),
            required_skills=("python",),
        )
    )

    assert result.eligible is True
    assert [(factor.key, factor.score, factor.reason_code) for factor in result.factors] == [
        ("skill", 100, "SKILL_OVERLAP_HIGH")
    ]
    assert result.confidence == 0.35


def test_no_available_factors_returns_low_confidence_without_inventing_a_score() -> None:
    result = score_match(MatchFeatures(target_id="empty"))

    assert result.eligible is True
    assert result.score == 0
    assert result.confidence == 0.0
    assert result.ranking_score == 0.0
    assert result.factors == ()
    assert result.missing_information == (
        "skill",
        "direction",
        "availability",
        "professional",
        "experience",
        "collaboration",
    )
    assert result.information_sufficient is False


@pytest.mark.parametrize(
    ("features", "message"),
    [
        (MatchFeatures(target_id="bad", direction_score=101), "direction_score"),
        (
            MatchFeatures(target_id="bad", candidate_hours_per_week=-1, required_hours_per_week=8),
            "candidate_hours_per_week",
        ),
        (
            MatchFeatures(target_id="bad", candidate_hours_per_week=8, required_hours_per_week=0),
            "required_hours_per_week",
        ),
        (MatchFeatures(target_id=" "), "target_id"),
        (
            MatchFeatures(
                target_id="bad-reason",
                constraints=(ConstraintResult("block", False, "BLOCKED_BY_USER"),),
            ),
            "safe public code",
        ),
    ],
)
def test_invalid_normalized_inputs_are_rejected(features: MatchFeatures, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        score_match(features)


def test_same_input_is_deterministic_and_constraint_reasons_are_stable() -> None:
    features = MatchFeatures(
        target_id="stable",
        candidate_skills=(" Python ", "PYTHON", "MySQL"),
        desired_skills=("mysql", "python"),
        constraints=(
            ConstraintResult("visibility", False, "CANDIDATE_NOT_ELIGIBLE"),
            ConstraintResult("status", False, "TARGET_NOT_AVAILABLE"),
            ConstraintResult("duplicate", False, "CANDIDATE_NOT_ELIGIBLE"),
        ),
    )

    first = score_match(features)
    second = score_match(features)

    assert first == second
    assert first.exclusion_reasons == ("CANDIDATE_NOT_ELIGIBLE", "TARGET_NOT_AVAILABLE")
