from datetime import datetime
import re
from typing import Annotated, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator


RolePreference = Literal["LEADER", "MEMBER", "FLEXIBLE"]
ProjectStatus = Literal["DRAFT", "PUBLISHED", "CLOSED"]
RoleStatus = Literal["OPEN", "CLOSED"]
MemberStatus = Literal["ACTIVE"]
InvitationStatus = Literal["PENDING", "ACCEPTED", "REJECTED", "EXPIRED", "CANCELLED"]
InvitationBox = Literal["SENT", "RECEIVED"]
ContactMethodType = Literal["WECHAT", "QQ", "EMAIL"]
ContactExchangeStatus = Literal["PENDING", "ACCEPTED", "REJECTED", "CANCELLED"]
ContactExchangeBox = Literal["SENT", "RECEIVED"]
StructuredLabel = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]


def normalize_label(value: str) -> str:
    return value.strip().casefold()


def validate_unique_labels(values: list[str], field_name: str) -> list[str]:
    normalized = [normalize_label(value) for value in values]
    if any(not value for value in normalized):
        raise ValueError(f"{field_name} must not contain empty values")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return [value.strip() for value in values]


class AvailabilitySlot(BaseModel):
    timezone: Literal["Asia/Shanghai"] = "Asia/Shanghai"
    weekday: int = Field(ge=1, le=7)
    startMinute: int = Field(ge=0, le=1439)
    endMinute: int = Field(ge=1, le=1440)

    @model_validator(mode="after")
    def validate_range(self):
        if self.startMinute >= self.endMinute:
            raise ValueError("startMinute must be before endMinute")
        return self


def validate_availability_slots(values: list[AvailabilitySlot], field_name: str) -> list[AvailabilitySlot]:
    ordered = sorted(values, key=lambda item: (item.timezone, item.weekday, item.startMinute, item.endMinute))
    previous_key: tuple[str, int] | None = None
    latest_end = -1
    for current in ordered:
        current_key = (current.timezone, current.weekday)
        if current_key != previous_key:
            previous_key = current_key
            latest_end = -1
        if current.startMinute < latest_end:
            raise ValueError(f"{field_name} must not contain overlapping slots")
        latest_end = max(latest_end, current.endMinute)
    return values


class ApiError(BaseModel):
    code: str
    message: str
    details: list[dict[str, str]] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ApiError
    requestId: str


DataT = TypeVar("DataT")


class Envelope(BaseModel, Generic[DataT]):
    model_config = ConfigDict(extra="forbid")
    data: DataT
    meta: dict[str, object] = Field(default_factory=dict)
    requestId: str


class HealthData(BaseModel):
    status: str
    storeBackend: str | None = None


class LogoutData(BaseModel):
    loggedOut: bool


class AccountDeletionRequestData(BaseModel):
    id: str
    status: Literal["PENDING", "CANCELLED", "COMPLETED"]
    requestedAt: datetime


class BlockRequest(BaseModel):
    blockedUserId: str = Field(min_length=1, max_length=64)


class BlockData(BaseModel):
    blockedUserId: str
    createdAt: datetime


class UnblockData(BaseModel):
    blockedUserId: str
    removed: bool


class ReportRequest(BaseModel):
    targetType: Literal["USER", "PROJECT", "MESSAGE"]
    targetId: str = Field(min_length=1, max_length=64)
    reason: Literal["SPAM", "HARASSMENT", "FRAUD", "INAPPROPRIATE_CONTENT", "OTHER"]
    description: str = Field(default="", max_length=500)

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class ReportData(BaseModel):
    id: str
    targetType: Literal["USER", "PROJECT", "MESSAGE"]
    targetId: str
    reason: Literal["SPAM", "HARASSMENT", "FRAUD", "INAPPROPRIATE_CONTENT", "OTHER"]
    status: Literal["PENDING", "REVIEWED", "DISMISSED", "ACTIONED"]
    createdAt: datetime


class InvitationCreateRequest(BaseModel):
    projectId: str = Field(min_length=1, max_length=64)
    roleId: str = Field(min_length=1, max_length=64)
    inviteeUserId: str = Field(min_length=1, max_length=64)


class InvitationData(BaseModel):
    id: str
    projectId: str
    roleId: str
    inviterUserId: str
    inviteeUserId: str
    status: InvitationStatus
    expiresAt: datetime
    createdAt: datetime
    respondedAt: datetime | None = None


class InvitationSummaryData(InvitationData):
    projectTitle: str
    roleName: str
    box: InvitationBox
    peerDisplayName: str


class ContactMethod(BaseModel):
    type: ContactMethodType
    value: str = Field(min_length=1, max_length=254)

    @field_validator("value", mode="before")
    @classmethod
    def strip_value(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_for_type(self):
        if self.type == "WECHAT" and not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{5,19}", self.value):
            raise ValueError("WECHAT value must be 6..20 supported characters and start with a letter")
        if self.type == "QQ" and not re.fullmatch(r"[1-9][0-9]{4,11}", self.value):
            raise ValueError("QQ value must be 5..12 digits and cannot start with zero")
        if self.type == "EMAIL" and not re.fullmatch(
            r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+",
            self.value,
        ):
            raise ValueError("EMAIL value must be a valid email address")
        return self


class ContactCardPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    methods: list[ContactMethod] = Field(min_length=1, max_length=3)

    @field_validator("methods")
    @classmethod
    def validate_unique_types(cls, value: list[ContactMethod]) -> list[ContactMethod]:
        method_types = [item.type for item in value]
        if len(set(method_types)) != len(method_types):
            raise ValueError("methods must not contain duplicate types")
        return value


class ContactCardUpdate(ContactCardPayload):
    version: int = Field(default=0, ge=0)


class ContactCardData(ContactCardPayload):
    version: int = Field(ge=1)
    updatedAt: datetime


class ContactExchangeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    projectId: str = Field(min_length=1, max_length=64)
    roleId: str = Field(min_length=1, max_length=64)


class ContactExchangeRequestRecord(BaseModel):
    id: str
    projectId: str
    roleId: str
    requesterUserId: str
    recipientUserId: str
    status: ContactExchangeStatus
    createdAt: datetime
    respondedAt: datetime | None = None


class ContactExchangeRequestData(ContactExchangeRequestRecord):
    projectTitle: str
    roleName: str
    box: ContactExchangeBox
    peerDisplayName: str
    peerContactCard: ContactCardData | None = None


class LoginRequest(BaseModel):
    code: str = Field(min_length=1, max_length=512)
    consentAccepted: bool


class SessionData(BaseModel):
    accessToken: str
    tokenType: Literal["Bearer"] = "Bearer"
    expiresIn: int = Field(ge=60)
    userId: str
    profileState: Literal["INCOMPLETE", "COMPLETE"]


class ProfilePayload(BaseModel):
    nickname: str = Field(min_length=1, max_length=24)
    school: str = Field(min_length=1, max_length=40)
    major: str = Field(min_length=1, max_length=40)
    grade: str = Field(min_length=1, max_length=16)
    skills: list[str] = Field(min_length=1, max_length=20)
    collaborationScenarios: list[str] = Field(min_length=1, max_length=10)
    rolePreference: RolePreference
    hoursPerWeek: int = Field(ge=1, le=40)
    bio: str = Field(default="", max_length=240)
    visibility: bool = False

    @field_validator("nickname", "school", "major", "grade", mode="before")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        return value.strip()


class ProfileData(ProfilePayload):
    version: int = Field(ge=1)
    updatedAt: datetime


class PublicProfileData(BaseModel):
    id: str
    nickname: str
    school: str
    major: str
    grade: str
    skills: list[str]
    collaborationScenarios: list[str]
    rolePreference: RolePreference
    hoursPerWeek: int = Field(ge=1, le=40)
    bio: str = ""
    updatedAt: datetime


class ProfileUpdate(ProfilePayload):
    version: int = Field(default=0, ge=0)


class MatchPreferencesPayload(BaseModel):
    desiredDirections: list[StructuredLabel] = Field(default_factory=list, max_length=10)
    availabilitySlots: list[AvailabilitySlot] = Field(default_factory=list, max_length=21)

    @field_validator("desiredDirections")
    @classmethod
    def validate_directions(cls, value: list[str]) -> list[str]:
        return validate_unique_labels(value, "desiredDirections")

    @field_validator("availabilitySlots")
    @classmethod
    def validate_slots(cls, value: list[AvailabilitySlot]) -> list[AvailabilitySlot]:
        return validate_availability_slots(value, "availabilitySlots")


class MatchPreferencesUpdate(MatchPreferencesPayload):
    version: int = Field(default=0, ge=0)


class MatchPreferencesData(MatchPreferencesPayload):
    version: int = Field(ge=1)
    updatedAt: datetime


class MatchResultData(BaseModel):
    targetType: Literal["PROFILE", "PROJECT_ROLE"]
    targetId: str
    targetSummary: dict[str, object]
    score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    informationSufficient: bool
    engineType: Literal["RULE", "ML_RANKER"]
    engineVersion: str
    modelVersion: str | None = None
    factors: list[dict[str, object]]
    missingInformation: list[str]


class RecommendationImpressionItem(BaseModel):
    targetType: Literal["PROFILE", "PROJECT_ROLE"]
    targetId: str = Field(min_length=1, max_length=64)
    position: int = Field(ge=1, le=50)


class RecommendationImpressionRequest(BaseModel):
    recommendationRequestId: str = Field(min_length=5, max_length=128)
    items: list[RecommendationImpressionItem] = Field(min_length=1, max_length=50)
    occurredAt: datetime

    @model_validator(mode="after")
    def validate_positions(self):
        positions = [item.position for item in self.items]
        if len(set(positions)) != len(positions):
            raise ValueError("items positions must be unique")
        targets = [(item.targetType, item.targetId) for item in self.items]
        if len(set(targets)) != len(targets):
            raise ValueError("items targets must be unique")
        return self


class RecommendationImpressionData(BaseModel):
    recommendationRequestId: str
    targetType: Literal["PROFILE", "PROJECT_ROLE"]
    targetId: str
    position: int
    recordedAt: datetime
    duplicate: bool = False


class RolePayload(BaseModel):
    name: str = Field(min_length=1, max_length=48)
    skills: list[StructuredLabel] = Field(min_length=1, max_length=20)
    headcount: int = Field(ge=1, le=100)
    hoursPerWeek: int = Field(ge=1, le=40)
    description: str = Field(default="", max_length=240)
    status: RoleStatus = "OPEN"
    requiredSkills: list[StructuredLabel] | None = Field(default=None, max_length=20)
    requiredAvailabilitySlots: list[AvailabilitySlot] | None = Field(default=None, max_length=21)
    collaborationRole: RolePreference | None = None

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, value: list[str]) -> list[str]:
        return validate_unique_labels(value, "skills")

    @field_validator("requiredSkills")
    @classmethod
    def validate_required_skills(cls, value: list[str] | None) -> list[str] | None:
        return None if value is None else validate_unique_labels(value, "requiredSkills")

    @field_validator("requiredAvailabilitySlots")
    @classmethod
    def validate_required_slots(cls, value: list[AvailabilitySlot] | None) -> list[AvailabilitySlot] | None:
        return None if value is None else validate_availability_slots(value, "requiredAvailabilitySlots")

    @model_validator(mode="after")
    def validate_required_subset(self):
        if self.requiredSkills is None:
            return self
        skills = {normalize_label(value) for value in self.skills}
        required = {normalize_label(value) for value in self.requiredSkills}
        if not required.issubset(skills):
            raise ValueError("requiredSkills must be a subset of skills")
        return self


class RoleData(RolePayload):
    id: str
    requiredSkills: list[str] = Field(default_factory=list)
    requiredAvailabilitySlots: list[AvailabilitySlot] = Field(default_factory=list)
    collaborationRole: RolePreference = "MEMBER"
    filledCount: int = Field(default=0, ge=0)
    remainingCount: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_capacity(self):
        if self.filledCount > self.headcount:
            raise ValueError("filledCount must not exceed headcount")
        if self.remainingCount != self.headcount - self.filledCount:
            raise ValueError("remainingCount must equal headcount minus filledCount")
        return self


class ProjectMemberData(BaseModel):
    id: str
    projectId: str
    roleId: str
    roleName: str
    userId: str
    status: MemberStatus = "ACTIVE"
    joinedAt: datetime


class InvitationAcceptData(BaseModel):
    invitation: InvitationData
    member: ProjectMemberData


class ConversationCreateRequest(BaseModel):
    projectId: str = Field(min_length=1, max_length=64)
    otherUserId: str = Field(min_length=1, max_length=64)


class ConversationData(BaseModel):
    id: str
    projectId: str
    participantUserIds: list[str] = Field(min_length=2, max_length=2)
    lastMessageAt: datetime | None = None
    createdAt: datetime


class MessageSendRequest(BaseModel):
    clientMessageId: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._:-]+$")
    content: str = Field(min_length=1, max_length=1000)

    @field_validator("content", mode="before")
    @classmethod
    def strip_content(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class MessageData(BaseModel):
    id: str
    conversationId: str
    senderUserId: str
    clientMessageId: str
    type: Literal["TEXT"] = "TEXT"
    content: str
    status: Literal["SENT"] = "SENT"
    createdAt: datetime


class ProjectPayload(BaseModel):
    title: str = Field(min_length=1, max_length=48)
    description: str = Field(min_length=1, max_length=600)
    direction: str = Field(min_length=1, max_length=32)
    competition: str = Field(default="", max_length=80)
    stage: str = Field(min_length=1, max_length=32)
    teamInfo: str = Field(default="", max_length=240)
    roles: list[RolePayload] = Field(min_length=1, max_length=20)
    collaborationScenarios: list[StructuredLabel] | None = Field(default=None, max_length=10)

    @field_validator("title", "description", "direction", "stage", mode="before")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        return value.strip()

    @field_validator("collaborationScenarios")
    @classmethod
    def validate_scenarios(cls, value: list[str] | None) -> list[str] | None:
        return None if value is None else validate_unique_labels(value, "collaborationScenarios")


class ProjectUpdate(ProjectPayload):
    version: int = Field(ge=1)


class ProjectData(ProjectPayload):
    id: str
    ownerId: str
    status: ProjectStatus
    version: int = Field(ge=1)
    publishedAt: datetime | None = None
    createdAt: datetime
    updatedAt: datetime
    roles: list[RoleData]
    collaborationScenarios: list[str] = Field(default_factory=list)


class ProjectAction(BaseModel):
    version: int = Field(ge=1)
