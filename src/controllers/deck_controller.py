from flask import Blueprint, jsonify, request

from extensions import db
from repositories.deck_repository import DeckRepository
from repositories.flashcard_repository import FlashcardRepository
from services.deck_service import DeckService
from services.errors import ServiceError

deck_bp = Blueprint("deck", __name__, url_prefix="/api")


def get_service() -> DeckService:
    return DeckService(
        deck_repository=DeckRepository(db.session),
        flashcard_repository=FlashcardRepository(db.session),
    )


@deck_bp.errorhandler(ServiceError)
def handle_service_error(error: ServiceError) -> tuple[object, int]:
    return jsonify({"error": {"code": error.code, "message": error.message}}), error.status_code


@deck_bp.get("/decks")
def list_decks() -> tuple[object, int]:
    decks = get_service().list_decks()
    return jsonify({"data": [deck.to_dict() for deck in decks]}), 200


@deck_bp.post("/decks")
def create_deck() -> tuple[object, int]:
    deck = get_service().create_deck(request.get_json(silent=True) or {})
    return jsonify({"data": deck.to_dict(include_flashcards=True)}), 201


@deck_bp.get("/decks/<int:deck_id>")
def get_deck(deck_id: int) -> tuple[object, int]:
    deck = get_service().get_deck(deck_id)
    return jsonify({"data": deck.to_dict(include_flashcards=True)}), 200


@deck_bp.post("/decks/<int:deck_id>/flashcards")
def add_flashcard(deck_id: int) -> tuple[object, int]:
    flashcard = get_service().add_flashcard(deck_id, request.get_json(silent=True) or {})
    return jsonify({"data": flashcard.to_dict()}), 201


@deck_bp.patch("/flashcards/<int:flashcard_id>/review")
def review_flashcard(flashcard_id: int) -> tuple[object, int]:
    flashcard = get_service().review_flashcard(flashcard_id, request.get_json(silent=True) or {})
    return jsonify({"data": flashcard.to_dict()}), 200


@deck_bp.delete("/flashcards/<int:flashcard_id>")
def delete_flashcard(flashcard_id: int) -> tuple[object, int]:
    get_service().delete_flashcard(flashcard_id)
    return jsonify({"data": {"deleted": True}}), 200
