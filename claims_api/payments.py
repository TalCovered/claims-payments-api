from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from claims_api.database import get_session
from claims_api.models import Payment, PaymentServiceLine
from claims_api.schemas import PaymentCreate, PaymentRead

router = APIRouter(prefix="/payments", tags=["Payments"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.post("", response_model=PaymentRead, status_code=201)
def create_payment(payload: PaymentCreate, session: SessionDependency) -> Payment:
    payment = Payment(
        **payload.model_dump(exclude={"service_lines"}),
        service_lines=[
            PaymentServiceLine(**line.model_dump()) for line in payload.service_lines
        ],
    )
    session.add(payment)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.scalar(
            select(Payment.id).where(
                Payment.payment_reference == payload.payment_reference
            )
        )
        if existing is not None:
            raise HTTPException(409, "Payment reference already exists") from None
        raise
    session.refresh(payment)
    return payment


@router.get("", response_model=list[PaymentRead])
def list_payments(
    session: SessionDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=2**63 - 1)] = 0,
) -> list[Payment]:
    return list(
        session.scalars(
            select(Payment)
            .options(selectinload(Payment.service_lines))
            .order_by(Payment.id)
            .offset(offset)
            .limit(limit)
        )
    )


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(
    payment_id: Annotated[int, Path(ge=1, le=2**63 - 1)], session: SessionDependency
) -> Payment:
    payment = session.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(404, "Payment not found")
    return payment
