from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

from .errors import ServiceError
from .matching import ConstraintResult, MatchDecision, MatchFeatures, score_match
from .schemas import (
    AvailabilitySlot,
    MatchPreferencesData,
    MatchResultData,
    ProfileData,
    ProjectData,
    PublicProfileData,
    RoleData,
)


MATCH_SNAPSHOT_TTL = timedelta(hours=24)
IMPRESSION_LOOKBACK = timedelta(hours=24)
IMPRESSION_FUTURE_SKEW = timedelta(minutes=5)


@dataclass
class MatchSnapshot:
    context: str
    created_at: datetime
    results: list[MatchResultData]
    viewer_user_id: str | None = None

    @property
    def expires_at(self) -> datetime:
        return self.created_at + MATCH_SNAPSHOT_TTL


def new_snapshot_id() -> str:
    return f"rrq_{token_urlsafe(24)}"


def encode_cursor(request_id: str, index: int) -> str:
    raw = f"{request_id}|{index}"
    return urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> tuple[str, int]:
    try:
        padding = "=" * (-len(cursor) % 4)
        request_id, raw_index = urlsafe_b64decode(cursor + padding).decode("utf-8").split("|", 1)
        index = int(raw_index)
        if not request_id.startswith("rrq_") or index < 0:
            raise ValueError
        return request_id, index
    except (ValueError, UnicodeDecodeError):
        raise ServiceError("INVALID_CURSOR", "推荐分页游标无效。", 422) from None


def page_snapshot(
    snapshots: dict[str, MatchSnapshot],
    context: str,
    results: list[MatchResultData] | None,
    limit: int,
    cursor: str | None,
    viewer_user_id: str | None = None,
) -> tuple[list[MatchResultData], str | None, str]:
    now = datetime.now(UTC)
    if cursor:
        request_id, start = decode_cursor(cursor)
        snapshot = snapshots.get(request_id)
        if snapshot is None or snapshot.context != context:
            raise ServiceError("INVALID_CURSOR", "推荐分页游标无效。", 422)
        if snapshot.expires_at <= now:
            snapshots.pop(request_id, None)
            raise ServiceError("RECOMMENDATION_EXPIRED", "推荐结果已过期，请重新加载。", 410)
        if results is not None:
            valid_ids = {item.targetId for item in results}
            snapshot.results = [item for item in snapshot.results if item.targetId in valid_ids]
    else:
        request_id = new_snapshot_id()
        snapshot = MatchSnapshot(
            context=context,
            created_at=now,
            results=results or [],
            viewer_user_id=viewer_user_id,
        )
        snapshots[request_id] = snapshot
        start = 0
    page = snapshot.results[start : start + limit]
    next_cursor = encode_cursor(request_id, start + limit) if start + limit < len(snapshot.results) else None
    return page, next_cursor, request_id


def validate_impression_time(occurred_at: datetime, now: datetime | None = None) -> datetime:
    """Normalize a client event timestamp and reject implausible clock drift."""
    if occurred_at.tzinfo is None:
        raise ServiceError("IMPRESSION_TIME_INVALID", "曝光时间必须包含时区。", 422)
    current = now or datetime.now(UTC)
    normalized = occurred_at.astimezone(UTC)
    if normalized < current - IMPRESSION_LOOKBACK or normalized > current + IMPRESSION_FUTURE_SKEW:
        raise ServiceError("IMPRESSION_TIME_INVALID", "曝光时间超出允许窗口。", 422)
    return normalized


def build_profile_match(
    project: ProjectData,
    role: RoleData,
    profile_id: str,
    profile: ProfileData | PublicProfileData,
    preferences: MatchPreferencesData | None,
) -> MatchResultData | None:
    if role.status != "OPEN" or role.remainingCount <= 0:
        return None
    if role.requiredAvailabilitySlots and not _slots_overlap(
        preferences.availabilitySlots if preferences else [], role.requiredAvailabilitySlots
    ):
        return None
    decision = score_match(
        MatchFeatures(
            target_id=profile_id,
            candidate_skills=tuple(profile.skills),
            desired_skills=tuple(role.skills),
            required_skills=tuple(role.requiredSkills),
            direction_score=_direction_score(preferences, project.direction),
            candidate_hours_per_week=profile.hoursPerWeek,
            required_hours_per_week=role.hoursPerWeek,
            collaboration_score=_collaboration_score(profile.rolePreference, role.collaborationRole),
        )
    )
    if not decision.eligible:
        return None
    return match_result(
        decision,
        target_type="PROFILE",
        target_summary={
            "id": profile_id,
            "nickname": profile.nickname,
            "skillLabels": profile.skills,
        },
    )


def build_project_match(
    profile_id: str,
    profile: ProfileData,
    preferences: MatchPreferencesData,
    project: ProjectData,
    role: RoleData,
) -> MatchResultData | None:
    if project.status != "PUBLISHED" or role.status != "OPEN" or role.remainingCount <= 0:
        return None
    if role.requiredAvailabilitySlots and not _slots_overlap(
        preferences.availabilitySlots, role.requiredAvailabilitySlots
    ):
        return None
    decision = score_match(
        MatchFeatures(
            target_id=role.id,
            candidate_skills=tuple(profile.skills),
            desired_skills=tuple(role.skills),
            required_skills=tuple(role.requiredSkills),
            direction_score=_direction_score(preferences, project.direction),
            candidate_hours_per_week=profile.hoursPerWeek,
            required_hours_per_week=role.hoursPerWeek,
            collaboration_score=_collaboration_score(profile.rolePreference, role.collaborationRole),
        )
    )
    if not decision.eligible:
        return None
    return match_result(
        decision,
        target_type="PROJECT_ROLE",
        target_summary={
            "projectId": project.id,
            "projectTitle": project.title,
            "roleId": role.id,
            "roleName": role.name,
            "direction": project.direction,
            "skillLabels": role.skills,
        },
    )


def match_result(decision: MatchDecision, target_type: str, target_summary: dict[str, object]) -> MatchResultData:
    return MatchResultData(
        targetType=target_type,
        targetId=decision.target_id,
        targetSummary=target_summary,
        score=decision.score,
        confidence=decision.confidence,
        informationSufficient=decision.information_sufficient,
        engineType=decision.engine_type,
        engineVersion=decision.engine_version,
        modelVersion=decision.model_version,
        factors=[
            {"key": factor.key, "score": factor.score, "reasonCode": factor.reason_code}
            for factor in decision.factors
        ],
        missingInformation=list(decision.missing_information),
    )


def _direction_score(preferences: MatchPreferencesData | None, direction: str) -> int | None:
    if preferences is None:
        return None
    return 100 if any(value.casefold() == direction.casefold() for value in preferences.desiredDirections) else 0


def _collaboration_score(candidate_role: str, required_role: str) -> int:
    if candidate_role == required_role or candidate_role == "FLEXIBLE" or required_role == "FLEXIBLE":
        return 100
    return 0


def _slots_overlap(candidate_slots: list[AvailabilitySlot], required_slots: list[AvailabilitySlot]) -> bool:
    return any(
        candidate.timezone == required.timezone
        and candidate.weekday == required.weekday
        and candidate.startMinute < required.endMinute
        and required.startMinute < candidate.endMinute
        for candidate in candidate_slots
        for required in required_slots
    )
