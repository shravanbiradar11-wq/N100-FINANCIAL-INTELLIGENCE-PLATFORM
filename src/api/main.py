import os
import sys
import time
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.abspath('.'))

from src.api.routers import health, companies, screener, sectors, reports_api

app = FastAPI(
    title="Nifty 100 Financial Analytics API",
    description="REST API providing multi-year financial ratios, NLP pros/cons, cash flow intelligence, and clustering data.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    print(f"[{request.method}] {request.url.path} - Completed in {duration:.4f}s with status {response.status_code}")
    return response

# Root route redirecting to interactive Swagger docs
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

app.include_router(health.router, prefix="/api/v1", tags=["Health & System"])
app.include_router(companies.router, prefix="/api/v1", tags=["Company Data"])
app.include_router(screener.router, prefix="/api/v1", tags=["Financial Screener"])
app.include_router(sectors.router, prefix="/api/v1", tags=["Sector Analytics"])
app.include_router(reports_api.router, prefix="/api/v1", tags=["Reports & Downloads"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
