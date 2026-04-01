from elasticsearch import AsyncElasticsearch

from app.config import settings

es_client = AsyncElasticsearch(
    hosts=[settings.elasticsearch_url],
    request_timeout=30,
    max_retries=3,
    retry_on_timeout=True,
)


async def get_es() -> AsyncElasticsearch:
    return es_client


async def close_es():
    await es_client.close()
