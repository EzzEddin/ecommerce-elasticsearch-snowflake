import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.elasticsearch import close_es, es_client
from app.services.search_service import SearchService
from app.api.v1.products import category_router, router as products_router
from app.api.v1.search import router as search_router
from app.api.v1.orders import router as orders_router
from app.api.v1.analytics import router as analytics_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
    try:
        search_service = SearchService(es_client)
        await search_service.create_index()
        logger.info("Elasticsearch index ready")
    except Exception as e:
        logger.warning(f"Could not connect to Elasticsearch: {e}")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await close_es()


app = FastAPI(
    title="E-commerce Search & Analytics API",
    description=(
        "A production-grade REST API demonstrating Elasticsearch for product search "
        "and Snowflake for sales analytics. Built with FastAPI, PostgreSQL, "
        "Elasticsearch, and Snowflake."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 routes
API_V1_PREFIX = "/api/v1"
app.include_router(products_router, prefix=API_V1_PREFIX)
app.include_router(category_router, prefix=API_V1_PREFIX)
app.include_router(search_router, prefix=API_V1_PREFIX)
app.include_router(orders_router, prefix=API_V1_PREFIX)
app.include_router(analytics_router, prefix=API_V1_PREFIX)


@app.get("/health", tags=["Health"])
async def health_check():
    health = {"status": "healthy", "services": {}}

    # Check Elasticsearch
    try:
        info = await es_client.info()
        health["services"]["elasticsearch"] = {
            "status": "connected",
            "version": info["version"]["number"],
        }
    except Exception as e:
        health["services"]["elasticsearch"] = {
            "status": "disconnected",
            "error": str(e),
        }

    # Check Snowflake
    try:
        from app.core.snowflake import get_snowflake_connection

        conn = get_snowflake_connection()
        try:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT CURRENT_VERSION()")
                version = cursor.fetchone()[0]
            finally:
                cursor.close()
        finally:
            conn.close()
        health["services"]["snowflake"] = {
            "status": "connected",
            "version": version,
        }
    except Exception as e:
        health["services"]["snowflake"] = {
            "status": "disconnected",
            "error": str(e),
        }

    return health
