"""Independent source records, each owning an ordered set of service lines."""

from datetime import date

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from claims_api.database import Base


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    claim_reference: Mapped[str] = mapped_column(unique=True)
    patient_name: Mapped[str]
    date_of_service: Mapped[date]
    place_of_service: Mapped[str]
    service_lines: Mapped[list["ClaimServiceLine"]] = relationship(
        cascade="all, delete-orphan", order_by="ClaimServiceLine.line_number"
    )


class ClaimServiceLine(Base):
    __tablename__ = "claim_service_lines"
    __table_args__ = (
        UniqueConstraint("claim_id", "line_number"),
        CheckConstraint("line_number > 0"),
        CheckConstraint("billed_amount_cents >= 0"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"), index=True)
    line_number: Mapped[int]
    procedure_code: Mapped[str]
    billed_amount_cents: Mapped[int]


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_reference: Mapped[str] = mapped_column(unique=True)
    claim_reference: Mapped[str] = mapped_column(index=True)
    patient_name: Mapped[str]
    date_of_service: Mapped[date]
    place_of_service: Mapped[str]
    service_lines: Mapped[list["PaymentServiceLine"]] = relationship(
        cascade="all, delete-orphan", order_by="PaymentServiceLine.line_number"
    )


class PaymentServiceLine(Base):
    __tablename__ = "payment_service_lines"
    __table_args__ = (
        UniqueConstraint("payment_id", "line_number"),
        CheckConstraint("line_number > 0"),
        CheckConstraint("billed_amount_cents >= 0"),
        CheckConstraint("paid_amount_cents >= 0"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), index=True)
    line_number: Mapped[int]
    procedure_code: Mapped[str]
    billed_amount_cents: Mapped[int]
    paid_amount_cents: Mapped[int]
    denial_reason: Mapped[str | None]
