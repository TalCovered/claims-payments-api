"""Add synthetic records, preserving any records with existing references."""

from datetime import date

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from claims_api.database import create_tables, make_engine
from claims_api.models import Claim, ClaimServiceLine, Payment, PaymentServiceLine


def seed_database(engine: Engine) -> tuple[int, int]:
    create_tables(engine)
    claim_count = payment_count = 0
    examples = [
        ("CLM-1001", "Alex Morgan", [12000], []),
        ("CLM-1002", "Jamie Chen", [15000, 5000], [[6000, 1000], [2000, 0]]),
        ("CLM-1003", "Sam Rivera", [9000], [[9000]]),
        ("CLM-1004", "Taylor Brooks", [18000], [[0]]),
        ("CLM-1005", "Jordan Patel", [10000], [[11000]]),
    ]
    with Session(engine) as session, session.begin():
        for reference, patient, billed, payments in examples:
            fields = {
                "claim_reference": reference,
                "patient_name": patient,
                "date_of_service": date(2026, 8, 10),
                "place_of_service": "11",
            }
            if (
                session.scalar(
                    select(Claim.id).where(Claim.claim_reference == reference)
                )
                is None
            ):
                session.add(
                    Claim(
                        **fields,
                        service_lines=[
                            ClaimServiceLine(
                                line_number=i,
                                procedure_code="99213" if i == 1 else "85025",
                                billed_amount_cents=amount,
                            )
                            for i, amount in enumerate(billed, start=1)
                        ],
                    )
                )
                claim_count += 1

            for payment_number, paid in enumerate(payments, start=1):
                payment_reference = f"PMT-{reference[4:]}-{payment_number}"
                if (
                    session.scalar(
                        select(Payment.id).where(
                            Payment.payment_reference == payment_reference
                        )
                    )
                    is not None
                ):
                    continue
                session.add(
                    Payment(
                        **fields,
                        payment_reference=payment_reference,
                        service_lines=[
                            PaymentServiceLine(
                                line_number=i,
                                procedure_code="99213" if i == 1 else "85025",
                                billed_amount_cents=billed_amount,
                                paid_amount_cents=paid_amount,
                                denial_reason=(
                                    "Missing supporting documentation"
                                    if reference == "CLM-1004"
                                    else None
                                ),
                            )
                            for i, (billed_amount, paid_amount) in enumerate(
                                zip(billed, paid, strict=True), start=1
                            )
                        ],
                    )
                )
                payment_count += 1

        if (
            session.scalar(
                select(Payment.id).where(Payment.payment_reference == "PMT-UNMATCHED-1")
            )
            is None
        ):
            session.add(
                Payment(
                    payment_reference="PMT-UNMATCHED-1",
                    claim_reference="CLM-9000",
                    patient_name="Casey Nguyen",
                    date_of_service=date(2026, 8, 12),
                    place_of_service="22",
                    service_lines=[
                        PaymentServiceLine(
                            line_number=1,
                            procedure_code="99214",
                            billed_amount_cents=16000,
                            paid_amount_cents=8000,
                            denial_reason="Additional documentation required",
                        )
                    ],
                )
            )
            payment_count += 1
    return claim_count, payment_count


def main() -> None:
    engine = make_engine()
    try:
        claims, payments = seed_database(engine)
        print(f"Added {claims} claims and {payments} payments.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
