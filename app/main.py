from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
import os
from app.database import get_connection, init_db

# ── Prometheus Metrics ───────────────────────────────────────
# These are counters and histograms that track what your app is doing.
# Prometheus will scrape these numbers every 15 seconds.

REQUEST_COUNT = Counter(
    "app_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "app_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint"]
)

DB_QUERY_COUNT = Counter(
    "app_db_queries_total",
    "Total number of database queries",
    ["operation"]
)

# ── Startup Event ────────────────────────────────────────────
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("TESTING") != "true":
        init_db()
    yield

app = FastAPI(title="DevOps Demo App", lifespan=lifespan)

# ── Middleware — tracks every request ───────────────────────
@app.middleware("http")
async def track_requests(request, call_next):
    """
    This wraps every single request.
    Before the request: start a timer
    After the request: record how long it took + what status code came back
    """
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(
        endpoint=request.url.path
    ).observe(duration)

    return response

# ── Routes ───────────────────────────────────────────────────

@app.get("/")
def root():
    """Basic health check — just confirms the app is alive."""
    return {"status": "ok", "message": "DevOps demo app is running"}

@app.get("/health")
def health():
    """
    Health endpoint — checks if the app AND database are reachable.
    Load balancers and monitoring tools ping this to know if the app is healthy.
    """
    try:
        conn = get_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unreachable: {str(e)}")

@app.get("/cities")
def get_cities():
    """Returns all cities stored in the database."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, country, added_at FROM cities ORDER BY added_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    DB_QUERY_COUNT.labels(operation="select").inc()
    return [
        {"id": r[0], "name": r[1], "country": r[2], "added_at": str(r[3])}
        for r in rows
    ]

@app.post("/cities")
def add_city(name: str, country: str):
    """Adds a new city to the database."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO cities (name, country) VALUES (%s, %s) RETURNING id",
        (name, country)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    DB_QUERY_COUNT.labels(operation="insert").inc()
    return {"id": new_id, "name": name, "country": country}

@app.delete("/cities/{city_id}")
def delete_city(city_id: int):
    """Deletes a city by ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM cities WHERE id = %s RETURNING id", (city_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="City not found")
    DB_QUERY_COUNT.labels(operation="delete").inc()
    return {"deleted": city_id}

@app.get("/metrics")
def metrics():
    """
    This is the endpoint Prometheus scrapes every 15 seconds.
    It returns all your counters and histograms in a special text format
    that Prometheus understands.
    """
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)