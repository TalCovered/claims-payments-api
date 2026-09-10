from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from claims_api.database import get_session
from claims_api.models import Claim, ClaimServiceLine
from claims_api.schemas import ClaimCreate, ClaimRead

router = APIRouter(prefix="/claims", tags=["Claims"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.post("", response_model=ClaimRead, status_code=201)
def create_claim(payload: ClaimCreate, session: SessionDependency) -> Claim:
    claim = Claim(
        **payload.model_dump(exclude={"service_lines"}),
        service_lines=[
            ClaimServiceLine(**line.model_dump()) for line in payload.service_lines
        ],
    )
    session.add(claim)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.scalar(
            select(Claim.id).where(Claim.claim_reference == payload.claim_reference)
        )
        if existing is not None:
            raise HTTPException(409, "Claim reference already exists") from None
        raise
    session.refresh(claim)
    return claim


@router.get("", response_model=list[ClaimRead])
def list_claims(
    session: SessionDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=2**63 - 1)] = 0,
) -> list[Claim]:
    return list(
        session.scalars(
            select(Claim)
            .options(selectinload(Claim.service_lines))
            .order_by(Claim.id)
            .offset(offset)
            .limit(limit)
        )
    )


@router.get("/{claim_id}", response_model=ClaimRead)
def get_claim(
    claim_id: Annotated[int, Path(ge=1, le=2**63 - 1)], session: SessionDependency
) -> Claim:
    claim = session.get(Claim, claim_id)
    if claim is None:
        raise HTTPException(404, "Claim not found")
    return claim
