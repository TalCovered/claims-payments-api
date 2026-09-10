from contextlib import asynccontextmanager

from fastapi import FastAPI

from claims_api import claims, payments
from claims_api.database import create_tables, make_engine


def create_app(database_url: str | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = make_engine(database_url)
        app.state.engine = engine
        try:
            create_tables(engine)
            yield
        finally:
            engine.dispose()

    app = FastAPI(
        title="Claims and Payments API",
        description="Store claims and independently received payment records.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(claims.router)
    app.include_router(payments.router)
    return app


app = create_app()
