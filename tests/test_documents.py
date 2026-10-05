import pytest
from httpx import AsyncClient


BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["elasticsearch"] is True


@pytest.mark.asyncio
async def test_search():
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/documents/search",
            params={"q": "python"},
        )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) <= 20

    for document in data:
        assert "id" in document
        assert "rubrics" in document
        assert "text" in document
        assert "created_date" in document


@pytest.mark.asyncio
async def test_search_empty_query():
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/documents/search",
            params={"q": ""},
        )

    assert response.status_code == 422

@pytest.mark.asyncio
async def test_delete_document():
    async with AsyncClient(base_url=BASE_URL) as client:
        search_response = await client.get(
            "/documents/search",
            params={"q": "python"},
        )

        assert search_response.status_code == 200

        documents = search_response.json()

        if not documents:
            pytest.skip("No documents found for deletion test")

        document_id = documents[0]["id"]

        delete_response = await client.delete(
            f"/documents/{document_id}"
        )

        assert delete_response.status_code == 200

        result = delete_response.json()

        assert result["id"] == document_id

        second_delete_response = await client.delete(
            f"/documents/{document_id}"
        )

        assert second_delete_response.status_code == 404