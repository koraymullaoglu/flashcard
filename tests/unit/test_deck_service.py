from dataclasses import dataclass, field

import pytest

from services.deck_service import DeckService
from services.errors import ConflictError, NotFoundError, ValidationError
from services.s3_service import S3ExportResult


@dataclass
class FakeDeck:
    id: int
    name: str
    user_id: int
    description: str | None = None
    flashcards: list[object] = field(default_factory=list)


@dataclass
class FakeFlashcard:
    id: int
    deck_id: int
    front: str
    back: str
    difficulty: str = "new"
    review_count: int = 0
    last_reviewed_at: object = None
    next_review_at: object = None
    interval_days: float = 0.0
    deck: FakeDeck | None = None


class FakeDeckRepository:
    def __init__(self) -> None:
        self.decks: dict[int, FakeDeck] = {}

    def list(self, user_id: int) -> list[FakeDeck]:
        return [d for d in self.decks.values() if d.user_id == user_id]

    def get(self, deck_id: int) -> FakeDeck | None:
        return self.decks.get(deck_id)

    def get_by_name(self, name: str, user_id: int) -> FakeDeck | None:
        return next(
            (d for d in self.decks.values() if d.name == name and d.user_id == user_id),
            None,
        )

    def create(
        self, name: str, user_id: int, description: str | None = None
    ) -> FakeDeck:
        deck = FakeDeck(
            id=len(self.decks) + 1, name=name, description=description, user_id=user_id
        )
        self.decks[deck.id] = deck
        return deck


class FakeFlashcardRepository:
    def __init__(self) -> None:
        self.flashcards: dict[int, FakeFlashcard] = {}

    def get(self, flashcard_id: int) -> FakeFlashcard | None:
        return self.flashcards.get(flashcard_id)

    def create(self, deck_id: int, front: str, back: str) -> FakeFlashcard:
        flashcard = FakeFlashcard(
            id=len(self.flashcards) + 1,
            deck_id=deck_id,
            front=front,
            back=back,
        )
        self.flashcards[flashcard.id] = flashcard
        return flashcard

    def save(self, flashcard: FakeFlashcard) -> FakeFlashcard:
        self.flashcards[flashcard.id] = flashcard
        return flashcard

    def delete(self, flashcard: FakeFlashcard) -> None:
        del self.flashcards[flashcard.id]


class FakeS3Service:
    def __init__(self) -> None:
        self.exported_deck: FakeDeck | None = None
        self.exported_user_id: int | None = None

    def export_deck(self, deck: FakeDeck, user_id: int) -> S3ExportResult:
        self.exported_deck = deck
        self.exported_user_id = user_id
        return S3ExportResult(bucket="flashcard-exports", key="exports/test.json", etag="etag-1")


TEST_USER = 1


@pytest.fixture()
def service() -> DeckService:
    deck_repo = FakeDeckRepository()
    flashcard_repo = FakeFlashcardRepository()
    return DeckService(deck_repo, flashcard_repo)


@pytest.mark.unit
def test_create_deck_trims_name(service: DeckService) -> None:
    deck = service.create_deck({"name": "  Python  ", "description": "Temel kartlar"}, TEST_USER)

    assert deck.name == "Python"


@pytest.mark.unit
def test_create_deck_rejects_empty_name(service: DeckService) -> None:
    with pytest.raises(ValidationError):
        service.create_deck({"name": "   "}, TEST_USER)


@pytest.mark.unit
def test_create_deck_rejects_duplicate_name(service: DeckService) -> None:
    service.create_deck({"name": "Python"}, TEST_USER)

    with pytest.raises(ConflictError):
        service.create_deck({"name": "Python"}, TEST_USER)


@pytest.mark.unit
def test_add_flashcard_requires_existing_deck(service: DeckService) -> None:
    with pytest.raises(NotFoundError):
        service.add_flashcard(999, {"front": "Soru", "back": "Cevap"}, TEST_USER)


@pytest.mark.unit
def test_review_flashcard_updates_difficulty_and_count(service: DeckService) -> None:
    deck = service.create_deck({"name": "Python"}, TEST_USER)
    card_data = {"front": "Flask nedir?", "back": "Web framework"}
    flashcard = service.add_flashcard(deck.id, card_data, TEST_USER)
    flashcard.deck = deck

    reviewed = service.review_flashcard(flashcard.id, {"difficulty": "good"}, TEST_USER)

    assert reviewed.difficulty == "good"
    assert reviewed.review_count == 1
    assert reviewed.last_reviewed_at is not None
    assert reviewed.next_review_at is not None
    assert reviewed.interval_days == 2.5


@pytest.mark.unit
@pytest.mark.parametrize(
    "difficulty, expected_interval",
    [
        ("again", 0.0),
        ("hard", 1.2),
        ("good", 2.5),
        ("easy", 3.5),
    ],
)
def test_review_flashcard_sm2_intervals(
    service: DeckService, difficulty: str, expected_interval: float
) -> None:
    deck = service.create_deck({"name": "SM2"}, TEST_USER)
    flashcard = service.add_flashcard(deck.id, {"front": "S", "back": "C"}, TEST_USER)
    flashcard.deck = deck

    reviewed = service.review_flashcard(flashcard.id, {"difficulty": difficulty}, TEST_USER)

    assert reviewed.interval_days == expected_interval
    if difficulty == "again":
        assert reviewed.next_review_at is not None
    else:
        assert reviewed.next_review_at is not None


@pytest.mark.unit
def test_review_flashcard_builds_on_existing_interval(service: DeckService) -> None:
    deck = service.create_deck({"name": "Build"}, TEST_USER)
    flashcard = service.add_flashcard(deck.id, {"front": "S", "back": "C"}, TEST_USER)
    flashcard.deck = deck

    first = service.review_flashcard(flashcard.id, {"difficulty": "good"}, TEST_USER)
    assert first.interval_days == 2.5

    second = service.review_flashcard(flashcard.id, {"difficulty": "good"}, TEST_USER)
    assert second.interval_days == 2.5 * 2.5


@pytest.mark.unit
@pytest.mark.parametrize("difficulty", ["bad", "", "GOOD"])
def test_review_flashcard_rejects_invalid_difficulty(
    service: DeckService,
    difficulty: str,
) -> None:
    deck = service.create_deck({"name": "Python"}, TEST_USER)
    flashcard = service.add_flashcard(deck.id, {"front": "Soru", "back": "Cevap"}, TEST_USER)
    flashcard.deck = deck

    with pytest.raises(ValidationError):
        service.review_flashcard(flashcard.id, {"difficulty": difficulty}, TEST_USER)


@pytest.mark.unit
def test_export_deck_to_s3_checks_ownership_and_returns_result(service: DeckService) -> None:
    deck = service.create_deck({"name": "Export"}, TEST_USER)
    s3_service = FakeS3Service()

    result = service.export_deck_to_s3(deck.id, TEST_USER, s3_service)

    assert s3_service.exported_deck == deck
    assert s3_service.exported_user_id == TEST_USER
    assert result.bucket == "flashcard-exports"
    assert result.key == "exports/test.json"
