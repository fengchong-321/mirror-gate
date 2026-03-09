from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.api.v1 import mock, api_test, ui_test, auth, scheduler, dashboard, testcase, mock_compare, api_test_report
from app.services.mock_interceptor import MockInterceptor, MockCompareTool
from app.database import SessionLocal
from typing import Optional
import asyncio
import json
import httpx

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


async def compare_and_save(
    suite_id: int,
    method: str,
    path: str,
    mock_response: str,
    real_url: str,
    headers: dict,
    body: Optional[str],
):
    """Async function to request real API and save comparison record."""
    from app.models.mock_compare import MockCompareRecord

    db = SessionLocal()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Filter headers to remove hop-by-hop headers and host
            filtered_headers = {
                k: v for k, v in headers.items()
                if k.lower() not in ("host", "content-length", "transfer-encoding")
            }
            response = await client.request(
                method=method,
                url=real_url,
                headers=filtered_headers,
                content=body,
            )
            real_response = response.text

        result = MockCompareTool.compare_responses(mock_response, real_response)

        record = MockCompareRecord(
            suite_id=suite_id,
            path=path,
            method=method,
            mock_response=mock_response,
            real_response=real_response,
            differences=result["differences"],
            is_match=result["match"],
        )
        db.add(record)
        db.commit()
    except Exception as e:
        print(f"Compare error: {e}")
    finally:
        db.close()


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
            # Check if compare is enabled and trigger async comparison
            if mock_response.get("enable_compare") and mock_response.get("suite_id"):
                try:
                    # Reconstruct the real URL for comparison
                    # Use the original request URL without modifications
                    real_url = str(request.url)

                    asyncio.create_task(
                        compare_and_save(
                            suite_id=mock_response["suite_id"],
                            method=request.method,
                            path=request.url.path,
                            mock_response=mock_response.get("body", "{}"),
                            real_url=real_url,
                            headers=dict(request.headers),
                            body=body,
                        )
                    )
                except Exception as e:
                    print(f"Failed to trigger compare: {e}")

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
app.include_router(api_test_report.router, prefix="/api/v1")
app.include_router(ui_test.router, prefix="/api/v1")
app.include_router(scheduler.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(testcase.router, prefix="/api/v1")
app.include_router(mock_compare.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}
