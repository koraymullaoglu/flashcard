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

Coverage raporunu minimum `%70` eşik zorlamasıyla görmek için:

```bash
uv run pytest --cov-report=term-missing
```

Bu projede coverage `%70` altına düşerse `uv run pytest` komutu başarısız olur.

Sadece unit test:

```bash
uv run pytest tests/unit
```

Sadece integration test:

```bash
uv run pytest tests/integration
```

Docker ile gerçek PostgreSQL Testcontainers testlerini çalıştırmak istersen:

```bash
RUN_TESTCONTAINERS=true uv run pytest tests/integration
```

Bu testler varsayılan koşuda kapalıdır; böylece normal `uv run pytest` ve `uv run pytest tests/integration` akışları hızlı kalır. `RUN_TESTCONTAINERS=true` verdiğinde `tests/integration/test_postgres_container.py` içindeki gerçek PostgreSQL senaryoları da çalışır.

LocalStack ile S3 export entegrasyon testini çalıştır:

```bash
RUN_LOCALSTACK_TESTS=true uv run pytest tests/integration/test_s3_export.py
```

Sadece e2e test (HTTP seviyesi):

```bash
uv run pytest tests/e2e
```

### Tarayici (Browser) E2E Testleri

Playwright ile gercek tarayicida UI testleri. Ilk kez calistirmadan once tarayici binary'lerini yukle:

```bash
uv run playwright install chromium
```

Tarayici testlerini calistir:

```bash
uv run pytest tests/e2e/ -m browser -v
```

Tarayiciyi gorsel olarak izleyerek debug etmek icin:

```bash
uv run pytest tests/e2e/ -m browser -v --headed
```

Bu testler `@pytest.mark.browser` marker'ini kullanir; `-m browser` filtresiyle sadece tarayici testleri calisir. Projede 4 tarayici test dosyasi bulunur:

| Dosya | Kapsam |
|---|---|
| `tests/e2e/test_auth_ui.py` | Giris/kayit sayfasi, tab gecisi, hata durumlari, logout, redirect |
| `tests/e2e/test_deck_list_ui.py` | Deste listesi, bos durum, modal ile deste olusturma, navigasyon |
| `tests/e2e/test_deck_detail_ui.py` | Deste detayi, kart listesi, kart ekleme/silme modal'lari, istatistikler |
| `tests/e2e/test_study_mode_ui.py` | Calisma modu, kart cevirme, zorluk derecelendirme, ilerleme, tamamlanma |

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

Koleksiyonu Newman ile lokal olarak da otomatik koşturabilirsin:

```bash
uv run flask --app app init-db
uv run flask --app app run --debug
newman run postman/flashcard-api.postman_collection.json -e postman/flashcard-local.postman_environment.json --bail
```

CI içinde de aynı collection aynı environment dosyasıyla Newman üzerinden çalıştırılır; isteklerden biri ya da içindeki testlerden biri başarısız olursa workflow fail olur.

## Kubernetes / Minikube

Proje Argo CD GitOps ile yonetilir. Tum altyapi (PostgreSQL, LocalStack, Prometheus + Grafana) ve uygulama `k8s/argocd/` altindaki Application kaynaklari uzerinden deploy edilir.

| Namespace | Icerik |
|---|---|
| `argocd` | Argo CD'nin kendisi |
| `infrastructure` | PostgreSQL, LocalStack, Prometheus + Grafana |
| `flashcard` | Flask API uygulamasi |

### On kosullar

Minikube ve `argocd` CLI gereklidir:

```bash
# Arch / CachyOS
sudo pacman -S argocd

# macOS
brew install argocd

# Diger Linux
curl -sSL -o /tmp/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /tmp/argocd
sudo mv /tmp/argocd /usr/local/bin/argocd
```

### Hizli baslangic

```bash
./scripts/kubernetes-start.sh   # Minikube + Docker imaji + Argo CD kurulumu
./scripts/kubernetes-sync.sh    # Tum uygulamalari sync'le + durum kontrolu
```

Ardindan port forward ve erisim bilgileri icin:

```bash
./scripts/kubernetes-forward.sh   # Argo CD, Prometheus, Grafana port forward
./scripts/kubernetes-result.sh    # URL'ler ve credential'lar
```

### Scriptler

| Script | Yaptigi |
|---|---|
| `kubernetes-start.sh` | Minikube'u baslatir, Docker imajini build eder, Argo CD kurar, `argocd` CLI ile login olur |
| `kubernetes-sync.sh` | Tum Application'lari (postgres, localstack, monitoring, flashcard-api) sync'ler, `kubernetes-check.sh` ile durumu kontrol eder |
| `kubernetes-check.sh` | Tum namespace'lerde rollout durumu ve Argo CD Application health/sync status |
| `kubernetes-forward.sh` | Argo CD UI (8080), Prometheus (9090), Grafana (3000) icin port-forward baslatir |
| `kubernetes-result.sh` | Servis URL'leri ve credential'lari yazdirir |
| `kubernetes-smoke-test.sh` | `/health` endpoint'ine retry'li istek, Argo CD durumu, pod kontrolu — CI'da da kullanilir |
| `kubernetes-delete.sh` | Tum Argo CD uygulamalarini ve cluster'i siler |
| `kubernetes-test-with-k6.sh` | k6 ile yuk testi |

### Sonraki deploy'lar

Argo CD automated sync aktif. Main branch'e push yaptiginda degisiklikler otomatik sync'lenir.

### Servislere erisim

`kubernetes-forward.sh` ile acilan portlar:

| Servis | Port |
|---|---|
| Argo CD UI | `http://localhost:8080` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` (admin / `kubernetes-result.sh` den ogren) |
| Flashcard API | `minikube service flashcard-api -n flashcard --url` |

### Temizlik

```bash
./scripts/kubernetes-delete.sh
```

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

### LocalStack Komutlari

LocalStack S3 bucket ve objelerini `aws` CLI ile sorgulayabilirsin. `--endpoint-url` parametresiyle istekleri LocalStack'e yonlendir:

```bash
# LocalStack'in ayakta oldugunu ve hangi servislerin calistigini kontrol et
curl -s http://localhost:4566/_localstack/health | python3 -m json.tool

# S3 bucket'lari listele
aws --endpoint-url=http://localhost:4566 s3 ls

# Yeni bucket olustur (gerekirse)
aws --endpoint-url=http://localhost:4566 s3 mb s3://flashcard-exports

# Bucket icindeki objeleri listele
aws --endpoint-url=http://localhost:4566 s3 ls s3://flashcard-exports/ --recursive

# Export edilen objenin icerigini goruntule
aws --endpoint-url=http://localhost:4566 s3 cp s3://flashcard-exports/exports/user-1/deck-1-20250101T000000Z.json -

# LocalStack container loglarini takip et
docker compose logs -f localstack
```

Docker Compose ile gelen LocalStack sadece `s3` servisini acar (`SERVICES: s3`). Baska servislere ihtiyac duyarsan `docker-compose.yml` icindeki `SERVICES` ortam degiskenini guncellemen yeterli.

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
k8s/
├── argocd/                             # Argo CD Application kaynaklari
│   ├── app-of-apps.yaml               # Root app (bootstrapping)
│   ├── infrastructure-app.yaml        # PostgreSQL, LocalStack, Monitoring
│   └── flashcard-api-app.yaml         # Flask API uygulamasi
├── infrastructure/                    # Helm values dosyalari
│   ├── namespace.yaml
│   ├── postgres-values.yaml
│   ├── localstack-values.yaml
│   └── monitoring-values.yaml
├── apps/flashcard/                    # Kustomize overlay
│   ├── namespace.yaml
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   ├── servicemonitor.yaml
│   └── secrets/
│       └── flashcard-api-secret.yaml
└── bootstrap/
    └── argo-cd-install.sh             # Argo CD kurulumu
scripts/
├── kubernetes-start.sh                # Minikube + imaj build + Argo CD kurulumu
├── kubernetes-sync.sh                 # Tum app'leri sync + secret + durum kontrolu
├── kubernetes-check.sh                # Rollout + Argo CD durumu
├── kubernetes-forward.sh              # Port forward (Argo CD, Prometheus, Grafana)
├── kubernetes-result.sh               # URL'ler ve credential'lar
├── kubernetes-smoke-test.sh           # /health kontrolu + Argo CD durumu
├── kubernetes-delete.sh               # Tum kaynaklari temizle
└── kubernetes-test-with-k6.sh         # k6 load test
```
