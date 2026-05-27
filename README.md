# Flashcard

Flask ile monolitik ama katmanlı bir Flashcard uygulaması. Backend katmanlı mimari (controller → service → repository) kullanır; frontend ise aynı Flask uygulaması içinde Jinja2 şablonları ve Tailwind CSS (CDN) ile sunulur.

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

PostgreSQL ve LocalStack'i başlat:

```bash
docker compose up -d postgres localstack
```

Tabloları oluştur:

```bash
uv run flask --app app init-db
```

Uygulamayı çalıştır:

```bash
uv run flask --app app run --debug
```

Uygulama varsayılan olarak `http://127.0.0.1:5000` adresinde çalışır. Tarayıcıdan bu adrese giderek arayüzü kullanabilirsin.

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

LocalStack ile S3 export entegrasyon testini çalıştır:

```bash
RUN_LOCALSTACK_TESTS=true uv run pytest tests/integration/test_s3_export.py
```

Sadece e2e test:

```bash
uv run pytest tests/e2e
```

Lint kontrolü:

```bash
uv run ruff check .
```

Otomatik düzeltme:

```bash
uv run ruff check --fix .
```

## Postman

Postman içinde şu iki dosyayı import edebilirsin:

- `postman/flashcard-api.postman_collection.json`
- `postman/flashcard-local.postman_environment.json`

Collection içindeki istekler sırasıyla çalıştırıldığında `deck_id` ve `flashcard_id` environment değişkenleri otomatik set edilir.

## Kubernetes / Minikube

### Ön koşullar

Minikube başlat:

```bash
minikube start
eval $(minikube docker-env)
docker build -t flashcard-api:dev .
```

Helm repolarını ekle:

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

### PostgreSQL (Helm)

```bash
helm install postgres bitnami/postgresql \
  --set auth.database=flashcard \
  --set auth.username=flashcard \
  --set auth.password=flashcard \
  --set primary.persistence.size=1Gi
```

### Prometheus + Grafana (Helm)

```bash
helm install monitoring prometheus-community/kube-prometheus-stack
```

Prometheus'a eriş:

```bash
kubectl port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090 > /dev/null 2>&1 &
# http://localhost:9090
```

Grafana'ya eriş:

```bash
kubectl port-forward svc/monitoring-grafana 3000:80 > /dev/null 2>&1 &
# http://localhost:3000  (admin / prom-operator)
```

Dashboard import: Grafana → Dashboards → Import → `monitoring/grafana-dashboard.json`

### Flask API

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/app-secret.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/servicemonitor.yaml
```

Durum kontrolü:

```bash
kubectl rollout status deployment/flashcard-api
API_URL=$(minikube service flashcard-api --url)
curl "$API_URL/health"
curl "$API_URL/api/decks"
```

### Temizlik

```bash
helm uninstall postgres monitoring
kubectl delete -f k8s/
```

## Endpointler

### Sayfa (HTML)

| Yol | Açıklama |
|-----|----------|
| `GET /` | Deste listesi |
| `GET /decks/<deck_id>` | Deste detayı ve çalışma modu |

### API (JSON)

| Yol | Açıklama |
|-----|----------|
| `GET /health` | Sağlık kontrolü |
| `POST /api/auth/register` | Kullanıcı kaydı |
| `POST /api/auth/login` | Giriş (JWT token döner) |
| `POST /api/decks` | Yeni deste oluştur |
| `GET /api/decks` | Tüm desteleri listele |
| `GET /api/decks/<deck_id>` | Deste detayı (kartlarla birlikte). `?due_only=true` ile sadece tekrarı gelen kartlar |
| `POST /api/decks/<deck_id>/flashcards` | Desteye kart ekle |
| `POST /api/decks/<deck_id>/export` | Deste ve kartlarini JSON olarak S3 bucket'ina export et |
| `PATCH /api/flashcards/<flashcard_id>/review` | Kartı değerlendir |
| `DELETE /api/flashcards/<flashcard_id>` | Kartı sil |

Tüm `/api/*` endpoint'leri (health hariç) `Authorization: Bearer <token>` header'ı gerektirir.

## S3 Export

Uygulama deck ve flashcard snapshot'larini JSON olarak S3'e export edebilir. Docker Compose ile gelen LocalStack servisi sayesinde bunu AWS hesabina gerek olmadan lokal ortamda deneyebilirsin.

Varsayilan ayarlar:

- `S3_BUCKET_NAME=flashcard-exports`
- `S3_REGION=us-east-1`
- `S3_ENDPOINT_URL=http://localstack:4566`
- `S3_EXPORT_PREFIX=exports`

Ornek export istegi:

```bash
curl -X POST \
  http://127.0.0.1:5000/api/decks/1/export \
  -H "Authorization: Bearer <token>"
```

Basarili response `bucket`, `key` ve `s3_uri` doner. Obje iceriginde export zamani, `user_id`, deck bilgisi ve tum flashcard'lar bulunur.

## Frontend

Arayüz Flask uygulamasının içinde Jinja2 şablonları ile sunulur. Ayrı bir build adımı veya ek bağımlılık gerektirmez; Tailwind CSS, CDN üzerinden yüklenir.

### Şablonlar

```
src/templates/
├── base.html          # Ortak layout, navbar, Tailwind CDN, font
├── index.html         # Deste listesi + oluşturma modalı
└── deck_detail.html   # Kart listesi, çalışma modu, kart ekleme/silme
```

### Özellikler

- **Koyu tema** — zinc-950 tabanlı, göz yormayan tasarım
- **Kart çevirme animasyonu** — CSS 3D transform ile çalışma deneyimi
- **SM-2 aralıklı tekrar** — Zorluk derecelendirmesine göre otomatik tekrar planlaması (again/hard/good/easy)
- **Zorluk derecelendirme** — Tekrar / Zor / İyi / Kolay
- **Responsive** — mobil ve masaüstü uyumlu
- **Playwright uyumlu** — tüm interaktif elementlerde `data-testid`

### Playwright Test Selectors

Tüm interaktif elementlerde `data-testid` attribute'u bulunur. Başlıca selector'lar:

```
# Deste listesi
[data-testid="page-title"]
[data-testid="btn-open-create-deck"]
[data-testid="deck-grid"]
[data-testid="deck-card-{id}"]
[data-testid="form-create-deck"]
[data-testid="input-deck-name"]
[data-testid="btn-submit-deck"]
[data-testid="empty-state"]

# Deste detayı
[data-testid="deck-title"]
[data-testid="btn-study"]
[data-testid="btn-open-add-card"]
[data-testid="card-row-{id}"]
[data-testid="btn-delete-card-{id}"]
[data-testid="form-add-card"]

# Çalışma modu
[data-testid="study-view"]
[data-testid="study-card"]
[data-testid="btn-diff-again"]
[data-testid="btn-diff-easy"]
[data-testid="study-complete"]
```

## Proje Yapısı

```
src/
├── app.py                          # Flask uygulama fabrikası
├── config.py                       # Konfigürasyon
├── extensions.py                   # SQLAlchemy instance
├── models.py                       # User, Deck ve Flashcard modelleri
├── middleware/
│   └── auth.py                     # JWT auth decorator (require_auth)
├── controllers/
│   ├── auth_controller.py          # /api/auth/* endpointleri
│   ├── deck_controller.py          # /api/* JSON endpointleri
│   └── view_controller.py          # / ve /decks/<id> sayfa endpointleri
├── services/
│   ├── auth_service.py             # Kullanıcı kayıt/giriş iş mantığı
│   ├── deck_service.py             # Deste/kart iş mantığı
│   └── errors.py                   # Servis hataları
├── repositories/
│   ├── deck_repository.py          # Deck veritabanı işlemleri
│   └── flashcard_repository.py     # Flashcard veritabanı işlemleri
└── templates/
    ├── base.html                   # Ortak layout + navbar auth kontrolleri
    ├── auth.html                   # Giriş / kayıt sayfası
    ├── index.html                  # Deste listesi
    └── deck_detail.html            # Deste detay ve çalışma modu
```
