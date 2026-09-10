"""API validation and response shapes. Monetary values are integer USD cents."""

from datetime import date
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

NonBlank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Cents = Annotated[int, Field(strict=True, ge=0, le=2**63 - 1)]
LineNumber = Annotated[int, Field(strict=True, gt=0, le=2**63 - 1)]


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class ClaimLineCreate(APIModel):
    line_number: LineNumber
    procedure_code: NonBlank
    billed_amount_cents: Cents


class PaymentLineCreate(ClaimLineCreate):
    paid_amount_cents: Cents
    denial_reason: NonBlank | None = None


class RecordFields(APIModel):
    claim_reference: NonBlank
    patient_name: NonBlank
    date_of_service: date
    place_of_service: NonBlank


class ClaimCreate(RecordFields):
    service_lines: list[ClaimLineCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_line_numbers(self) -> Self:
        numbers = [line.line_number for line in self.service_lines]
        if len(numbers) != len(set(numbers)):
            raise ValueError("Service line numbers must be unique within a record")
        return self


class PaymentCreate(RecordFields):
    payment_reference: NonBlank
    service_lines: list[PaymentLineCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_line_numbers(self) -> Self:
        numbers = [line.line_number for line in self.service_lines]
        if len(numbers) != len(set(numbers)):
            raise ValueError("Service line numbers must be unique within a record")
        return self


class ClaimLineRead(ClaimLineCreate):
    id: int


class PaymentLineRead(PaymentLineCreate):
    id: int


class ClaimRead(RecordFields):
    id: int
    service_lines: list[ClaimLineRead]


class PaymentRead(RecordFields):
    id: int
    payment_reference: str
    service_lines: list[PaymentLineRead]
