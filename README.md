# Flashcard API

Bu proje, Test Mühendisliği dönem projesi için seçilen basit bir `Flashcard` mini servis başlangıcıdır. Flask ile monolitik ama katmanlı bir yapı kullanır: controller, service ve repository.

## Gereksinimler

- uv
- Docker ve Docker Compose
- PostgreSQL için varsayılan bağlantı: `postgresql+psycopg://flashcard:flashcard@localhost:5432/flashcard`

## Kurulum

```bash
uv python install 3.11
uv sync --group dev --python 3.11
cp .env.example .env
```

Bu projede `pyenv` kullanılmaz. Python sürümünü, `.venv` ortamını, dependency kurulumunu ve komut çalıştırmayı `uv` yönetir.

PostgreSQL'i başlat:

```bash
docker compose up -d postgres
```

Tabloları oluştur:

```bash
uv run flask --app app init-db
```

Uygulamayı çalıştır:

```bash
uv run flask --app app run --debug
```

API varsayılan olarak `http://127.0.0.1:5000` adresinde çalışır.

## Testler

Tüm testleri çalıştır:

```bash
uv run pytest
```

Sadece unit test:

```bash
uv run pytest tests/unit
```

Sadece integration test:

```bash
uv run pytest tests/integration
```

Docker ile gerçek PostgreSQL Testcontainers testi de çalışsın istersen:

```bash
RUN_TESTCONTAINERS=true uv run pytest tests/integration
```

Sadece e2e test:

```bash
uv run pytest tests/e2e
```

Lint kontrolü:

```bash
uv run ruff check .
```

## Postman

Postman içinde şu iki dosyayı import edebilirsin:

- `postman/flashcard-api.postman_collection.json`
- `postman/flashcard-local.postman_environment.json`

Collection içindeki istekler sırasıyla çalıştırıldığında `deck_id` ve `flashcard_id` environment değişkenleri otomatik set edilir.

## Endpointler

- `GET /health`
- `POST /api/decks`
- `GET /api/decks`
- `GET /api/decks/<deck_id>`
- `POST /api/decks/<deck_id>/flashcards`
- `PATCH /api/flashcards/<flashcard_id>/review`
- `DELETE /api/flashcards/<flashcard_id>`
