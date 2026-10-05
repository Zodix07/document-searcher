# Document Search Service

Простой поисковый сервис по текстовым документам.

Сервис позволяет:
- импортировать документы из CSV;
- хранить документы в PostgreSQL;
- индексировать текст документов в Elasticsearch;
- выполнять полнотекстовый поиск;
- получать до 20 найденных документов;
- сортировать результаты по дате создания;
- удалять документы из PostgreSQL и Elasticsearch;
- запускать сервис с помощью Docker Compose;
- получать OpenAPI-документацию.

## Стек

- Python 3.12
- FastAPI
- PostgreSQL 17
- SQLAlchemy
- asyncpg
- Elasticsearch 8.19
- Elasticsearch Python Client 8.x
- Docker
- Docker Compose
- pytest
- httpx

## Структура проекта

```text
document-searcher/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   └── elastic.py
│
├── data/
│   └── posts.csv
│
├── scripts/
│   ├── import_data.py
│   └── generate_docs.py
│
├── tests/
│   ├── __init__.py
│   └── test_documents.py
│
├── Dockerfile
├── docker-compose.yml
├── docs.json
├── requirements.txt
├── .dockerignore
├── .gitignore
└── README.md
```
## Архитектура

Сервис использует PostgreSQL для хранения полной информации о документах,
а Elasticsearch — для полнотекстового поиска.

                    ┌─────────────────┐
                    │     Client      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    FastAPI      │
                    └────────┬────────┘
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
          ┌───────────────┐     ┌───────────────┐
          │ Elasticsearch │     │  PostgreSQL   │
          │  text search  │     │ full document │
          └───────────────┘     └───────────────┘

При поиске Elasticsearch находит идентификаторы подходящих документов.
После этого полная информация загружается из PostgreSQL и сортируется
по created_date.

## Модель данных

Таблица documents содержит:

| Поле | Тип | Описание |
|------|-----|----------|
|id |	BIGINT |	Уникальный идентификатор |
|rubrics |	JSONB |	Массив рубрик |
|text |	TEXT	| Текст документа |
|created_date	| TIMESTAMP |	Дата создания |

Индекс documents содержит:

| Поле | Тип | Описание |
|------|-----|----------|
|id |	long |	Идентификатор документа |
|text	| text	| Текст для полнотекстового поиска |

Идентификатор документа в Elasticsearch совпадает с id в PostgreSQL.

## Запуск

Необходимы:
Docker
Docker Compose

1. Запустить сервисы

В корневой директории проекта выполнить:
```docker compose up -d --build```

Проверить состояние контейнеров:
```docker compose ps```

Должны быть запущены три сервиса:

- PostgreSQL
- Elasticsearch
- FastAPI application

2. Импортировать тестовые данные

После запуска контейнеров выполнить:
```docker compose run --rm app python scripts/import_data.py```

После успешного импорта будет выведено:
```Imported 1500 documents.```

Количество документов зависит от входного CSV-файла.

## API
### Проверка состояния сервиса
GET /health

Пример ответа:

{
  "status": "ok",
  "elasticsearch": true
}

### Поиск документов
```GET /documents/search?q=python```

Параметр:

q — текстовый поисковый запрос.

Сервис возвращает не более 20 документов.

Каждый документ содержит:

{
  "id": 1,
  "rubrics": [
    "example"
  ],
  "text": "Document text",
  "created_date": "2026-01-01T12:00:00"
}

Результаты сортируются по created_date от новых к старым.

### Удаление документа
```DELETE /documents/{id}```

Например:

```DELETE /documents/123```

Документ удаляется как из PostgreSQL, так и из Elasticsearch.

Если документ не найден, сервис возвращает HTTP 404.

## Swagger / OpenAPI

После запуска приложения интерактивная документация доступна по адресу:

http://localhost:8000/docs

Также доступна JSON-версия OpenAPI:

docs.json

Файл docs.json можно использовать для просмотра или импорта API в инструменты,
поддерживающие OpenAPI.

## Тестирование

Для запуска функциональных тестов необходимо, чтобы Docker-контейнеры
были запущены:

```docker compose up -d```

Затем выполнить:

```pytest```

Тесты проверяют:

- доступность сервиса;
- подключение Elasticsearch;
- выполнение поиска;
- структуру результатов поиска;
- обработку пустого поискового запроса.

## Генерация OpenAPI-документации

Для повторной генерации docs.json:

```python scripts/generate_docs.py```

## Остановка

Остановить контейнеры:

```docker compose down```

Для удаления контейнеров вместе с данными PostgreSQL и Elasticsearch:

```docker compose down -v```

## Переменные окружения

По умолчанию приложение использует:

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/document_search
ELASTICSEARCH_URL=http://localhost:9200

В Docker Compose значения автоматически переопределяются адресами
соответствующих контейнеров:

DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/document_search
ELASTICSEARCH_URL=http://elasticsearch:9200

## Особенности реализации
- Асинхронное взаимодействие с PostgreSQL через SQLAlchemy и asyncpg.
- Асинхронное взаимодействие с Elasticsearch.
- Полнотекстовый поиск выполняется Elasticsearch.
- Полные данные документов хранятся в PostgreSQL.
- Для входного CSV используется стандартный модуль csv.
- Поле rubrics преобразуется из строкового представления списка в массив.
- created_date преобразуется в объект datetime.
- FastAPI автоматически предоставляет OpenAPI-схему.