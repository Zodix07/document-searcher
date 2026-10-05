from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import delete, select

from app.database import async_session, create_tables
from app.elastic import (
    INDEX_NAME,
    close_elasticsearch,
    create_index,
    es,
)
from app.models import Document


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    await create_index()

    yield

    await close_elasticsearch()


app = FastAPI(
    title="Document Search Service",
    description="Простой поисковый сервис по текстам документов.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    """
    Проверка работоспособности сервиса.
    """
    try:
        elasticsearch_ok = await es.ping()
    except Exception:
        elasticsearch_ok = False

    return {
        "status": "ok",
        "elasticsearch": elasticsearch_ok,
    }


@app.get("/documents/search")
async def search_documents(
    q: str = Query(
        ...,
        min_length=1,
        description="Текстовый поисковый запрос",
    ),
):
    """
    Поиск документов по тексту через Elasticsearch.
    """

    query = q.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Search query must not be empty",
        )

    try:
        response = await es.search(
            index=INDEX_NAME,
            query={
                "match": {
                    "text": {
                        "query": query,
                    }
                }
            },
            size=10000,
            _source=False,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Elasticsearch error: {exc}",
        ) from exc

    ids = [
        int(hit["_id"])
        for hit in response["hits"]["hits"]
    ]

    if not ids:
        return []

    async with async_session() as session:
        result = await session.execute(
            select(Document)
            .where(Document.id.in_(ids))
            .order_by(Document.created_date.desc())
            .limit(20)
        )

        documents = result.scalars().all()

    return [
        {
            "id": document.id,
            "rubrics": document.rubrics,
            "text": document.text,
            "created_date": document.created_date,
        }
        for document in documents
    ]


@app.delete("/documents/{document_id}")
async def delete_document(document_id: int):
    """
    Удаление документа из PostgreSQL и Elasticsearch.
    """

    async with async_session() as session:
        result = await session.execute(
            select(Document).where(Document.id == document_id)
        )

        document = result.scalar_one_or_none()

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document not found",
            )

        await session.execute(
            delete(Document).where(Document.id == document_id)
        )

        await session.commit()

    try:
        await es.delete(
            index=INDEX_NAME,
            id=str(document_id),
            ignore=[404],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Elasticsearch error: {exc}",
        ) from exc

    return {
        "message": "Document deleted",
        "id": document_id,
    }