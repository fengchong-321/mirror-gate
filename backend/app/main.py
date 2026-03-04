from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.api.v1 import mock, api_test, ui_test, auth, scheduler, dashboard, testcase
from app.services.mock_interceptor import MockInterceptor
from app.database import SessionLocal
import asyncio
import json

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

# Get allowed origins from settings or use localhost for development
allowed_origins = ["http://localhost:3000", "http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def mock_interceptor_middleware(request: Request, call_next):
    """Mock interceptor middleware for API gateway.

    Intercepts API requests and returns mock responses if matching rules exist.
    """
    # Only intercept API requests
    if not request.url.path.startswith("/api/"):
        return await call_next(request)

    # Exclude Mock management API itself
    if request.url.path.startswith("/api/v1/mock/"):
        return await call_next(request)

    db = SessionLocal()
    try:
        interceptor = MockInterceptor(db)

        # Get request information
        method = request.method
        path = request.url.path
        headers = dict(request.headers)
        query_params = dict(request.query_params)

        # Get request body (only for methods with body)
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            body = body.decode("utf-8") if body else None

        # Get client information
        client_info = {
            "clientId": request.headers.get("x-client-id", ""),
            "userId": request.headers.get("x-user-id", ""),
            "vid": request.headers.get("x-vid", ""),
        }

        # Check if mock matches
        mock_response = interceptor.get_mock_response(
            method, path, headers, body, query_params, client_info
        )

        if mock_response:
            # Simulate delay
            if mock_response.get("delay_ms", 0) > 0:
                await asyncio.sleep(mock_response["delay_ms"] / 1000)

            return JSONResponse(
                content=json.loads(mock_response["body"]) if mock_response["body"] else {},
                status_code=mock_response.get("status_code", 200),
                headers=mock_response.get("headers", {}),
            )
    finally:
        db.close()

    return await call_next(request)


# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(mock.router, prefix="/api/v1")
app.include_router(api_test.router, prefix="/api/v1")
app.include_router(ui_test.router, prefix="/api/v1")
app.include_router(scheduler.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(testcase.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}
