from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.exceptions import AppError
from app.api.middleware.logging import LoggingMiddleware
from app.api.v1.routers.portfolio import router as portfolio_router
from app.api.v1.routers.corporate_actions import router as corporate_actions_router
from app.api.v1.routers.market_data import router as market_data_router

app = FastAPI(
    title="Passive Wealth Reconstruction Engine",
    description="A backend-focused financial analytics engine to reconstruct long-term shareholder wealth for Indian investors.",
    version="0.1.0"
)

# Register CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register logging middleware
app.add_middleware(LoggingMiddleware)

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    if not errors:
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "VALIDATION_ERROR", "message": str(exc), "field": None}}
        )
    first_error = errors[0]
    field = first_error["loc"][-1] if first_error["loc"] else None
    msg = first_error["msg"]
    
    code = "VALIDATION_ERROR"
    if field == "exchange":
        code = "INVALID_EXCHANGE"
    elif field == "buy_date":
        code = "INVALID_BUY_DATE"
    elif field == "quantity":
        code = "INVALID_QUANTITY"
    elif field == "buy_price_per_share":
        code = "INVALID_QUANTITY"
    elif field == "ticker":
        code = "INVALID_TICKER"
        
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": code,
                "message": msg,
                "field": str(field) if field else None
            }
        }
    )

@app.exception_handler(AppError)
async def app_error_exception_handler(request: Request, exc: AppError):
    status_code = 500
    if exc.code == "NOT_FOUND":
        status_code = 404
        code = "NO_DATA_AVAILABLE"
    elif exc.code == "VALIDATION_ERROR":
        status_code = 422
        code = "VALIDATION_ERROR"
    elif exc.code == "INVALID_TICKER":
        status_code = 422
        code = "INVALID_TICKER"
    elif exc.code == "INVALID_BUY_DATE":
        status_code = 422
        code = "INVALID_BUY_DATE"
    elif exc.code == "DATA_FETCH_FAILED":
        status_code = 503
        code = "DATA_FETCH_FAILED"
    else:
        code = exc.code

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": exc.message,
                "field": None
            }
        }
    )

# Register routers under /api/v1 prefix
app.include_router(portfolio_router, prefix="/api/v1/portfolio", tags=["Portfolio"])
app.include_router(corporate_actions_router, prefix="/api/v1/corporate-actions", tags=["Corporate Actions"])
app.include_router(market_data_router, prefix="/api/v1/market-data", tags=["Market Data"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
