# Claims and Payments API

A small revenue cycle management API built with Python, FastAPI, SQLAlchemy, and
SQLite. It stores claims and independent payment records, each with service lines.

## Concepts

- **Provider**: whoever delivers the care, such as a doctor, nurse, or clinic.
- **Payer**: an insurance company.
- **Claim**: a provider's bill to a payer for one patient visit.
- **Service line**: one billed item on a claim, like a procedure with its charge.
  A claim has one or more.
- **Payment**: the payer's response to a claim, matched by claim reference. One
  claim can get several payments.
- **Payment line**: the payer's decision on one service line: what was billed,
  what was paid, and why anything was denied.

Example: Dr. Lee (provider) sends claim `CLM-1001` with two service lines to Acme
Health (payer). Acme replies with payment `PAY-5001`, which pays the office visit
in part and denies the blood test.

| Line | Procedure | Billed (claim) | Paid (payment) | Denial reason |
| --- | --- | --- | --- | --- |
| 1 | `99213` office visit | $150.00 | $120.00 | |
| 2 | `85025` blood count | $40.00 | $0.00 | Not medically necessary |

## Run locally

Requires Python 3.12 or newer. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m claims_api.seed
python -m uvicorn claims_api.main:app --reload
```

On Windows, activate with `.venv\Scripts\Activate.ps1` in PowerShell.

Open [the API explorer](http://127.0.0.1:8000/docs) for request schemas and to try
the endpoints.

Tables are created automatically. The optional seed command adds five fictional
claims and six payments, skipping existing references when run again.

The database defaults to `claims.db` in the current working directory. Set
`DATABASE_URL` to use another SQLite file, such as `sqlite:///./local.db`.
Use the same configuration and working directory for seeding and running the API.
Startup creates missing tables but does not migrate existing schemas.

## API

| Method | Path | Behavior |
| --- | --- | --- |
| POST | `/claims` | Create a claim with service lines |
| GET | `/claims` | List claims |
| GET | `/claims/{id}` | Retrieve a claim by internal ID |
| POST | `/payments` | Create a payment with service lines |
| GET | `/payments` | List payments |
| GET | `/payments/{id}` | Retrieve a payment by internal ID |

Lists include service lines and return arrays ordered by internal ID. Pagination
uses `limit` (default 20, maximum 100) and `offset` (default 0). Service lines are
ordered by line number.

Creation is atomic and returns `201`. Missing records return `404`, duplicate
business references return `409`, and invalid input returns `422`.

## Data model

- Claims have a unique claim reference, patient name, date of service, place of
  service, and one or more lines with a procedure code and billed amount.
- Payments have a unique payment reference and their own copy of patient and
  service details. Each line includes billed and paid amounts and an optional
  denial reason.
- A payment's claim reference is an external reference, not a foreign key.
  Multiple payments can refer to one claim, and payments can arrive before claims.
  Payment details are not checked against or synchronized with claims.
- Each line belongs to its parent record and has a positive line number unique
  within that parent. Date and place of service apply to all the parent's lines.
  Payment lines do not link to claim lines.
- Money is nonnegative integer USD cents: `15000` means $150.00. Zero, partial,
  and excess payments are allowed. A denial reason can accompany a partial payment.
- Required strings are trimmed and nonblank; references are case-sensitive.
  Dates use `YYYY-MM-DD`. Procedure and place-of-service codes are strings without
  external catalog validation.

## Code layout

In `claims_api`, `main.py` creates the app, `database.py` configures SQLite and
request-scoped sessions, `models.py` defines the tables, and `schemas.py` defines
validation and response shapes. `claims.py` and `payments.py` contain the routes;
`seed.py` supplies sample data.

This local API has no authentication, update/delete endpoints, or integrations.
It does not model adjustments, refunds, or insurance/patient responsibility.
