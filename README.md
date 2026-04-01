# E-commerce Search & Analytics Platform

A production-grade REST API and React frontend demonstrating **Elasticsearch** for product search and **Snowflake** for sales analytics. Built with modern Python backend patterns.

![Search Page](imgs/search-page.png)

## Architecture

```
React (TypeScript) Frontend
        │
        ▼
FastAPI (Python) REST API
   │         │          │
   ▼         ▼          ▼
PostgreSQL  Elasticsearch  Snowflake
(products,  (search index, (sales analytics,
 orders,     autocomplete,  aggregated reports,
 inventory)  faceted search) historical data)
```

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| **Primary DB** | PostgreSQL 16 |
| **Search Engine** | Elasticsearch 8.12 |
| **Data Warehouse** | Snowflake |
| **Frontend** | React 18, TypeScript, TailwindCSS, Recharts |
| **Testing** | pytest, pytest-asyncio |
| **Infrastructure** | Docker Compose |

## Features

### Elasticsearch-Powered Search
- **Full-text search** with fuzzy matching and relevance scoring
- **Autocomplete** using edge n-gram tokenizer
- **Faceted search** — filter by category, brand, price range, rating
- **Search highlighting** for matched terms
- **Configurable sorting** — relevance, price, rating, newest
- **Bulk indexing** with PostgreSQL → ES sync

![Product Detail](imgs/product-detail.png)

### Snowflake Analytics
- **Revenue over time** — daily/weekly/monthly aggregation
- **Top-selling products** — ranked by revenue
- **Category performance** — revenue, units sold, avg order value
- **Star schema** — `PRODUCT_DIMENSIONS` + `SALES_FACTS` tables
- **Batch sync pipeline** — PostgreSQL → Snowflake via `executemany` for fast ingestion
- **Materialized views** — pre-aggregated daily revenue for fast dashboard queries

![Analytics Dashboard](imgs/analytics-dashboard.png)

### Kibana (Dev Tools)
- **Index inspection** — browse indexed products, verify mappings
- **Query testing** — interactively test Elasticsearch queries
- **Cluster monitoring** — shard health, index stats
- Access at http://localhost:5601

### Backend Architecture
- **Controller-Service-Repository** pattern (clean separation of concerns)
- **Async everywhere** — asyncpg, async Elasticsearch client
- **Pydantic v2** schemas with strict validation
- **Alembic** database migrations
- **Auto-generated** OpenAPI/Swagger documentation

## Prerequisites

- **Docker Desktop** — for PostgreSQL and Elasticsearch
- **Python 3.12+**
- **Node.js 18+** and npm
- **Snowflake account** — [free 30-day trial](https://signup.snowflake.com/)

## Quick Start

### 1. Start Infrastructure

```bash
docker-compose up -d
```

This starts PostgreSQL (port 5432), Elasticsearch (port 9200), and Kibana (port 5601).

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from example and update Snowflake creds)
copy .env.example .env        # Windows
# cp .env.example .env        # Mac/Linux

# Seed database with sample data (~500 products, 250 orders)
python -m seed_data.seed

# Run the API server
uvicorn app.main:app --reload --port 8000
```

### 3. Reindex Elasticsearch

After seeding, trigger a reindex via the API:

```bash
# Mac/Linux
curl -X POST http://localhost:8000/api/v1/search/reindex

# Windows PowerShell (curl is aliased to Invoke-WebRequest)
curl.exe -X POST http://localhost:8000/api/v1/search/reindex
# or
Invoke-RestMethod -Method POST -Uri http://localhost:8000/api/v1/search/reindex
```

Or visit http://localhost:8000/docs and use the Swagger UI.

![Swagger UI](imgs/swagger-ui.png)

### 4. Snowflake Setup (Optional)

1. Sign up at https://signup.snowflake.com/
2. Update `.env` with your Snowflake credentials:
   - `SNOWFLAKE_ACCOUNT` — your account identifier (e.g. `abc12345.us-east-1`)
   - `SNOWFLAKE_USER` / `SNOWFLAKE_PASSWORD` — login credentials
   - `SNOWFLAKE_WAREHOUSE` — compute warehouse (default: `COMPUTE_WH`)
   - `SNOWFLAKE_ROLE` — role with CREATE DATABASE privileges (default: `SYSADMIN`)
3. Sync data to Snowflake (creates schema + syncs products & orders):

```bash
curl.exe -X POST http://localhost:8000/api/v1/analytics/sync
```

This creates a `ECOM_ANALYTICS` database with a star schema:
- **`PRODUCT_DIMENSIONS`** — product_id, name, brand, category, price, sku
- **`SALES_FACTS`** — order_id, product_id, quantity, unit_price, total_price, order_date
- **`DAILY_REVENUE_MV`** — materialized view for pre-aggregated daily revenue

![Snowflake Data](imgs/snowflake-data.png)

### 5. Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

Open http://localhost:5173

## API Endpoints

### Products
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/products` | List products (paginated) |
| GET | `/api/v1/products/{id}` | Get product detail |
| POST | `/api/v1/products` | Create product |
| PUT | `/api/v1/products/{id}` | Update product |
| DELETE | `/api/v1/products/{id}` | Delete product |

### Search (Elasticsearch)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/search?q=...` | Full-text search with facets |
| GET | `/api/v1/search/autocomplete?q=...` | Autocomplete suggestions |
| POST | `/api/v1/search/reindex` | Rebuild ES index from PostgreSQL |

### Analytics (Snowflake)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/analytics/revenue?period=daily` | Revenue over time |
| GET | `/api/v1/analytics/top-products?limit=10` | Top products by revenue |
| GET | `/api/v1/analytics/categories` | Category performance |
| POST | `/api/v1/analytics/sync` | Sync data to Snowflake |
| POST | `/api/v1/analytics/setup` | Create Snowflake schema |

### Other
| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc documentation |

![Health Check](imgs/health-check.png)

## Using Kibana

Kibana runs at http://localhost:5601. Navigate to **Dev Tools** (Menu → Management → Dev Tools) to test queries:

```json
// Count indexed products
GET ecom_products/_count

// Search with fuzzy matching
GET ecom_products/_search
{
  "query": {
    "multi_match": {
      "query": "wireless headphones",
      "fields": ["name^3", "description", "brand^2"],
      "fuzziness": "AUTO"
    }
  }
}

// View category and brand facets
GET ecom_products/_search
{
  "size": 0,
  "aggs": {
    "categories": { "terms": { "field": "category.keyword" } },
    "brands": { "terms": { "field": "brand.keyword", "size": 20 } },
    "avg_price": { "avg": { "field": "price" } }
  }
}

// Test autocomplete
GET ecom_products/_search
{
  "query": { "match": { "name.autocomplete": { "query": "pre", "operator": "and" } } },
  "_source": ["name"]
}
```

![Kibana Dev Tools](imgs/kibana-dev-tools.png)

![Kibana Index Management](imgs/kibana-index.png)

## Environment Variables

All config is in `backend/.env` (copy from `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://ecom_user:ecom_pass@localhost:5432/ecom_db` | Async PostgreSQL connection |
| `DATABASE_URL_SYNC` | `postgresql+psycopg2://...` | Sync PostgreSQL (used by Alembic) |
| `ELASTICSEARCH_URL` | `http://localhost:9200` | Elasticsearch endpoint |
| `ELASTICSEARCH_INDEX_PREFIX` | `ecom` | Index name prefix |
| `SNOWFLAKE_ACCOUNT` | — | Snowflake account identifier |
| `SNOWFLAKE_USER` | — | Snowflake username |
| `SNOWFLAKE_PASSWORD` | — | Snowflake password |
| `SNOWFLAKE_DATABASE` | `ECOM_ANALYTICS` | Snowflake database name |
| `SNOWFLAKE_SCHEMA` | `PUBLIC` | Snowflake schema |
| `SNOWFLAKE_WAREHOUSE` | `COMPUTE_WH` | Snowflake compute warehouse |
| `SNOWFLAKE_ROLE` | `SYSADMIN` | Snowflake role |

## Running Tests

```bash
cd backend
.venv\Scripts\activate   # Windows
pytest -v
pytest --cov=app tests/
```

## Project Structure

```
├── docker-compose.yml          # PostgreSQL + Elasticsearch + Kibana
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── config.py           # Settings (pydantic-settings)
│   │   ├── api/v1/             # Route handlers (controllers)
│   │   │   ├── products.py     # Product CRUD endpoints
│   │   │   ├── search.py       # ES search endpoints
│   │   │   ├── orders.py       # Order endpoints
│   │   │   └── analytics.py    # Snowflake analytics endpoints
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Business logic layer
│   │   │   ├── product_service.py
│   │   │   ├── search_service.py
│   │   │   ├── order_service.py
│   │   │   └── analytics_service.py
│   │   ├── repositories/       # Data access layer
│   │   └── core/               # DB, ES, Snowflake connections
│   ├── tests/                  # pytest test suite
│   ├── seed_data/              # Database seeding script
│   ├── alembic/                # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Main app with routing
│   │   ├── api.ts              # API client
│   │   └── pages/
│   │       ├── SearchPage.tsx      # Product search with facets
│   │       ├── ProductDetailPage.tsx
│   │       └── AnalyticsPage.tsx   # Snowflake analytics dashboard
│   ├── package.json
│   └── tailwind.config.js
└── README.md
```

## Design Decisions

- **FastAPI** over Django/Flask — async-first, auto-docs, modern Python type hints
- **Controller-Service-Repository** — clean separation between HTTP layer, business logic, and data access
- **Async I/O** — non-blocking DB and search queries for high concurrency
- **Pydantic v2** — 5-50x faster validation than v1
- **Edge n-gram tokenizer** for autocomplete — production-grade approach vs simple prefix matching
- **Star schema in Snowflake** — proper data warehousing with fact/dimension tables
- **Batch sync (`executemany`)** — efficient bulk ingestion to Snowflake instead of row-by-row inserts
- **Unsplash product images** — category-specific product photos with no people

## Troubleshooting

| Issue | Solution |
|---|---|
| `curl -X POST` fails in PowerShell | Use `curl.exe -X POST` or `Invoke-RestMethod -Method POST -Uri <url>` |
| Elasticsearch connection refused | Ensure Docker is running: `docker-compose up -d` |
| Snowflake "Object does not exist" | Run sync first: `POST /api/v1/analytics/sync` (creates DB + schema) |
| Frontend lint errors in IDE | Run `cd frontend && npm install` to install dependencies |
| Seed script fails on DB connection | Check that PostgreSQL container is healthy: `docker ps` |
| Analytics page shows "Unavailable" | Verify Snowflake credentials in `backend/.env` and run sync |
| ES reindex returns empty results | Make sure seed data exists in PostgreSQL first |

## Ports Reference

| Service | Port | URL |
|---|---|---|
| FastAPI backend | 8000 | http://localhost:8000 |
| Swagger UI | 8000 | http://localhost:8000/docs |
| React frontend | 5173 | http://localhost:5173 |
| PostgreSQL | 5432 | — |
| Elasticsearch | 9200 | http://localhost:9200 |
| Kibana | 5601 | http://localhost:5601 |

## License

MIT
