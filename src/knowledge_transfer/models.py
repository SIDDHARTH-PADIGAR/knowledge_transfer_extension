
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class EvidenceType(str, Enum):
    SOP = "sop"
    TRANSCRIPT = "transcript"
    VERIFICATION_RECORD = "verification_record"
    TASK_OUTPUT = "task_output"


class ReadinessStatus(str, Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"


class VerificationOutcome(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    INCOMPLETE = "incomplete"


class GapStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class Evidence(Record):
    id: str
    source: str
    evidence_type: EvidenceType
    content: str = Field(min_length=1)
    recorded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class Responsibility(Record):
    id: str
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    successor: Optional[str] = None
    evidence_ids: list[str] = Field(default_factory=list)


class KnowledgeGap(Record):
    id: str
    responsibility_id: str
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    status: GapStatus = GapStatus.OPEN
    resolution_note: Optional[str] = None
    resolved_at: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_resolution(self):
        if self.status == GapStatus.RESOLVED:
            if not self.resolution_note or not self.resolution_note.strip():
                raise ValueError("Resolved gaps require a resolution note.")
            if self.resolved_at is None:
                raise ValueError("Resolved gaps require a resolution timestamp.")
        return self


class VerificationRecord(Record):
    id: str
    responsibility_id: str
    successor: str = Field(min_length=1)
    assessment_criteria: str = Field(min_length=1)
    outcome: VerificationOutcome
    evidence_ids: list[str] = Field(min_length=1)
    reviewer: str = Field(min_length=1)
    verified_at: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_verification(self):
        if self.outcome == VerificationOutcome.PASSED:
            if self.verified_at is None:
                raise ValueError(
                    "A passing assessment requires a verification timestamp."
                )
        elif self.verified_at is not None:
            raise ValueError(
                "Only a passed assessment may have a verification timestamp."
            )
        return self

    @property
    def readiness(self) -> ReadinessStatus:
        if (
            self.outcome == VerificationOutcome.PASSED
            and self.verified_at is not None
            and self.evidence_ids
            and self.assessment_criteria.strip()
            and self.reviewer.strip()
        ):
            return ReadinessStatus.VERIFIED

        return ReadinessStatus.UNVERIFIED
