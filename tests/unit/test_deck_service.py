from dataclasses import dataclass, field

import pytest

from services.deck_service import DeckService
from services.errors import ConflictError, NotFoundError, ValidationError


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
