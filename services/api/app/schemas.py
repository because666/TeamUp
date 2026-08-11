from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


RolePreference = Literal["LEADER", "MEMBER", "FLEXIBLE"]
ProjectStatus = Literal["DRAFT", "PUBLISHED", "CLOSED"]
RoleStatus = Literal["OPEN", "CLOSED"]


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


class ProfileUpdate(ProfilePayload):
    version: int = Field(default=0, ge=0)


class RolePayload(BaseModel):
    name: str = Field(min_length=1, max_length=48)
    skills: list[str] = Field(min_length=1, max_length=20)
    headcount: int = Field(ge=1, le=100)
    hoursPerWeek: int = Field(ge=1, le=40)
    description: str = Field(default="", max_length=240)
    status: RoleStatus = "OPEN"


class RoleData(RolePayload):
    id: str


class ProjectPayload(BaseModel):
    title: str = Field(min_length=1, max_length=48)
    description: str = Field(min_length=1, max_length=600)
    direction: str = Field(min_length=1, max_length=32)
    competition: str = Field(default="", max_length=80)
    stage: str = Field(min_length=1, max_length=32)
    teamInfo: str = Field(default="", max_length=240)
    roles: list[RolePayload] = Field(min_length=1, max_length=20)

    @field_validator("title", "description", "direction", "stage", mode="before")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        return value.strip()


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


class ProjectAction(BaseModel):
    version: int = Field(ge=1)
