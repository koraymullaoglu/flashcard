from datetime import datetime, timezone

from models import Deck, Flashcard
from repositories.deck_repository import DeckRepository
from repositories.flashcard_repository import FlashcardRepository
from services.errors import ConflictError, NotFoundError, ValidationError

ALLOWED_DIFFICULTIES = {"again", "hard", "good", "easy"}


class DeckService:
    def __init__(
        self,
        deck_repository: DeckRepository,
        flashcard_repository: FlashcardRepository,
    ):
        self.deck_repository = deck_repository
        self.flashcard_repository = flashcard_repository

    def list_decks(self, user_id: int) -> list[Deck]:
        return self.deck_repository.list(user_id)

    def _get_owned_deck(self, deck_id: int, user_id: int) -> Deck:
        deck = self.deck_repository.get(deck_id)
        if deck is None:
            raise NotFoundError("Deck bulunamadi.")
        if deck.user_id != user_id:
            raise NotFoundError("Deck bulunamadi.")
        return deck

    def get_deck(self, deck_id: int, user_id: int) -> Deck:
        return self._get_owned_deck(deck_id, user_id)

    def create_deck(self, payload: dict[str, object], user_id: int) -> Deck:
        name = self._required_string(payload, "name", max_length=120)
        description = self._optional_string(payload, "description", max_length=255)

        if self.deck_repository.get_by_name(name, user_id):
            raise ConflictError("Bu isimde bir deck zaten var.")

        return self.deck_repository.create(name=name, user_id=user_id, description=description)

    def add_flashcard(self, deck_id: int, payload: dict[str, object], user_id: int) -> Flashcard:
        self._get_owned_deck(deck_id, user_id)
        front = self._required_string(payload, "front", max_length=500)
        back = self._required_string(payload, "back", max_length=500)
        return self.flashcard_repository.create(deck_id=deck_id, front=front, back=back)

    def review_flashcard(
        self, flashcard_id: int, payload: dict[str, object], user_id: int
    ) -> Flashcard:
        flashcard = self.flashcard_repository.get(flashcard_id)
        if flashcard is None or flashcard.deck.user_id != user_id:
            raise NotFoundError("Flashcard bulunamadi.")

        difficulty = self._required_string(payload, "difficulty", max_length=20)
        if difficulty not in ALLOWED_DIFFICULTIES:
            allowed = ", ".join(sorted(ALLOWED_DIFFICULTIES))
            raise ValidationError(f"difficulty su degerlerden biri olmali: {allowed}.")

        flashcard.difficulty = difficulty
        flashcard.review_count += 1
        flashcard.last_reviewed_at = datetime.now(timezone.utc)
        return self.flashcard_repository.save(flashcard)

    def delete_flashcard(self, flashcard_id: int, user_id: int) -> None:
        flashcard = self.flashcard_repository.get(flashcard_id)
        if flashcard is None or flashcard.deck.user_id != user_id:
            raise NotFoundError("Flashcard bulunamadi.")
        self.flashcard_repository.delete(flashcard)

    @staticmethod
    def _required_string(payload: dict[str, object], field: str, max_length: int) -> str:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{field} zorunlu ve bos olmayan bir string olmali.")
        value = value.strip()
        if len(value) > max_length:
            raise ValidationError(f"{field} en fazla {max_length} karakter olabilir.")
        return value

    @staticmethod
    def _optional_string(payload: dict[str, object], field: str, max_length: int) -> str | None:
        value = payload.get(field)
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValidationError(f"{field} string olmali.")
        value = value.strip()
        if len(value) > max_length:
            raise ValidationError(f"{field} en fazla {max_length} karakter olabilir.")
        return value or None
