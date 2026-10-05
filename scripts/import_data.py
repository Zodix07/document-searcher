import ast
import asyncio
import csv
import datetime
import sys
from pathlib import Path

from sqlalchemy import delete

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import async_session, create_tables
from app.elastic import INDEX_NAME, create_index, es
from app.models import Document


CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "posts.csv"


async def import_data():
    await create_tables()
    await create_index()

    async with async_session() as session:
        await session.execute(delete(Document))
        await session.commit()

    await es.indices.delete(
        index=INDEX_NAME,
        ignore=[404],
    )

    await create_index()

    documents = []

    with open(
        CSV_PATH,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            rubrics = ast.literal_eval(row["rubrics"])

            created_date = datetime.datetime.strptime(
                row["created_date"],
                "%Y-%m-%d %H:%M:%S",
            )

            documents.append(
                Document(
                    rubrics=rubrics,
                    text=row["text"],
                    created_date=created_date,
                )
            )

    async with async_session() as session:
        session.add_all(documents)
        await session.flush()

        for document in documents:
            await es.index(
                index=INDEX_NAME,
                id=str(document.id),
                document={
                    "id": document.id,
                    "text": document.text,
                },
            )

        await session.commit()

    await es.indices.refresh(index=INDEX_NAME)

    print(f"Imported {len(documents)} documents.")


async def main():
    try:
        await import_data()
    finally:
        await es.close()


if __name__ == "__main__":
    asyncio.run(main())