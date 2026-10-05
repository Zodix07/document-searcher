import os

from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import NotFoundError


ELASTICSEARCH_URL = os.getenv(
    "ELASTICSEARCH_URL",
    "http://localhost:9200",
)

INDEX_NAME = "documents"


es = AsyncElasticsearch(
    ELASTICSEARCH_URL,
)


async def create_index() -> None:
    try:
        await es.indices.get(index=INDEX_NAME)
        return
    except NotFoundError:
        pass

    await es.indices.create(
        index=INDEX_NAME,
        mappings={
            "properties": {
                "id": {
                    "type": "long",
                },
                "text": {
                    "type": "text",
                },
            }
        },
    )


async def close_elasticsearch() -> None:
    await es.close()