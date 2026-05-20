from dataclasses import dataclass, field

import pytest

from services.deck_service import DeckService
from services.errors import ConflictError, NotFoundError, ValidationError


@dataclass
class FakeDeck:
    id: int
    name: str
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


class FakeDeckRepository:
    def __init__(self) -> None:
        self.decks: dict[int, FakeDeck] = {}

    def list(self) -> list[FakeDeck]:
        return list(self.decks.values())

    def get(self, deck_id: int) -> FakeDeck | None:
        return self.decks.get(deck_id)

    def get_by_name(self, name: str) -> FakeDeck | None:
        return next((deck for deck in self.decks.values() if deck.name == name), None)

    def create(self, name: str, description: str | None = None) -> FakeDeck:
        deck = FakeDeck(id=len(self.decks) + 1, name=name, description=description)
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


@pytest.fixture()
def service() -> DeckService:
    deck_repo = FakeDeckRepository()
    flashcard_repo = FakeFlashcardRepository()
    return DeckService(deck_repo, flashcard_repo)


@pytest.mark.unit
def test_create_deck_trims_name(service: DeckService) -> None:
    deck = service.create_deck({"name": "  Python  ", "description": "Temel kartlar"})

    assert deck.name == "Python"


@pytest.mark.unit
def test_create_deck_rejects_empty_name(service: DeckService) -> None:
    with pytest.raises(ValidationError):
        service.create_deck({"name": "   "})


@pytest.mark.unit
def test_create_deck_rejects_duplicate_name(service: DeckService) -> None:
    service.create_deck({"name": "Python"})

    with pytest.raises(ConflictError):
        service.create_deck({"name": "Python"})


@pytest.mark.unit
def test_add_flashcard_requires_existing_deck(service: DeckService) -> None:
    with pytest.raises(NotFoundError):
        service.add_flashcard(999, {"front": "Soru", "back": "Cevap"})


@pytest.mark.unit
def test_review_flashcard_updates_difficulty_and_count(service: DeckService) -> None:
    deck = service.create_deck({"name": "Python"})
    flashcard = service.add_flashcard(deck.id, {"front": "Flask nedir?", "back": "Web framework"})

    reviewed = service.review_flashcard(flashcard.id, {"difficulty": "good"})

    assert reviewed.difficulty == "good"
    assert reviewed.review_count == 1


@pytest.mark.unit
@pytest.mark.parametrize("difficulty", ["bad", "", "GOOD"])
def test_review_flashcard_rejects_invalid_difficulty(
    service: DeckService,
    difficulty: str,
) -> None:
    deck = service.create_deck({"name": "Python"})
    flashcard = service.add_flashcard(deck.id, {"front": "Soru", "back": "Cevap"})

    with pytest.raises(ValidationError):
        service.review_flashcard(flashcard.id, {"difficulty": difficulty})
