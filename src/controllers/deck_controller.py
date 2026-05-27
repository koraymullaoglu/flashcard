from flask import Blueprint, current_app, g, jsonify, request

from extensions import db
from middleware.auth import require_auth
from repositories.deck_repository import DeckRepository
from repositories.flashcard_repository import FlashcardRepository
from services.deck_service import DeckService
from services.errors import ServiceError
from services.s3_service import S3Service

deck_bp = Blueprint("deck", __name__, url_prefix="/api")


def get_service() -> DeckService:
    return DeckService(
        deck_repository=DeckRepository(db.session),
        flashcard_repository=FlashcardRepository(db.session),
    )


def get_s3_service() -> S3Service:
    return S3Service(
        bucket_name=current_app.config["S3_BUCKET_NAME"],
        region=current_app.config["S3_REGION"],
        endpoint_url=current_app.config.get("S3_ENDPOINT_URL"),
        access_key_id=current_app.config.get("AWS_ACCESS_KEY_ID"),
        secret_access_key=current_app.config.get("AWS_SECRET_ACCESS_KEY"),
        export_prefix=current_app.config["S3_EXPORT_PREFIX"],
    )


@deck_bp.errorhandler(ServiceError)
def handle_service_error(error: ServiceError) -> tuple[object, int]:
    return jsonify({"error": {"code": error.code, "message": error.message}}), error.status_code


@deck_bp.get("/decks")
@require_auth
def list_decks() -> tuple[object, int]:
    decks = get_service().list_decks(g.current_user_id)
    return jsonify({"data": [deck.to_dict() for deck in decks]}), 200


@deck_bp.post("/decks")
@require_auth
def create_deck() -> tuple[object, int]:
    deck = get_service().create_deck(request.get_json(silent=True) or {}, g.current_user_id)
    return jsonify({"data": deck.to_dict(include_flashcards=True)}), 201


@deck_bp.get("/decks/<int:deck_id>")
@require_auth
def get_deck(deck_id: int) -> tuple[object, int]:
    due_only = request.args.get("due_only", "").lower() == "true"
    deck = get_service().get_deck(deck_id, g.current_user_id, due_only=due_only)
    return jsonify({"data": deck.to_dict(include_flashcards=True)}), 200


@deck_bp.post("/decks/<int:deck_id>/flashcards")
@require_auth
def add_flashcard(deck_id: int) -> tuple[object, int]:
    payload = request.get_json(silent=True) or {}
    flashcard = get_service().add_flashcard(deck_id, payload, g.current_user_id)
    return jsonify({"data": flashcard.to_dict()}), 201


@deck_bp.patch("/flashcards/<int:flashcard_id>/review")
@require_auth
def review_flashcard(flashcard_id: int) -> tuple[object, int]:
    payload = request.get_json(silent=True) or {}
    flashcard = get_service().review_flashcard(flashcard_id, payload, g.current_user_id)
    return jsonify({"data": flashcard.to_dict()}), 200


@deck_bp.delete("/flashcards/<int:flashcard_id>")
@require_auth
def delete_flashcard(flashcard_id: int) -> tuple[object, int]:
    get_service().delete_flashcard(flashcard_id, g.current_user_id)
    return jsonify({"data": {"deleted": True}}), 200


@deck_bp.post("/decks/<int:deck_id>/export")
@require_auth
def export_deck(deck_id: int) -> tuple[object, int]:
    export_result = get_service().export_deck_to_s3(
        deck_id=deck_id,
        user_id=g.current_user_id,
        s3_service=get_s3_service(),
    )
    return jsonify({"data": export_result.to_dict()}), 200
