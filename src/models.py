from datetime import datetime, timezone

from extensions import db


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Deck(db.Model):
    __tablename__ = "decks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    flashcards = db.relationship(
        "Flashcard",
        back_populates="deck",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_dict(self, include_flashcards: bool = False) -> dict[str, object]:
        data: dict[str, object] = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "flashcard_count": len(self.flashcards),
        }
        if include_flashcards:
            data["flashcards"] = [card.to_dict() for card in self.flashcards]
        return data


class Flashcard(db.Model):
    __tablename__ = "flashcards"

    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(db.Integer, db.ForeignKey("decks.id"), nullable=False, index=True)
    front = db.Column(db.String(500), nullable=False)
    back = db.Column(db.String(500), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, default="new")
    review_count = db.Column(db.Integer, nullable=False, default=0)
    last_reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    deck = db.relationship("Deck", back_populates="flashcards")

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "deck_id": self.deck_id,
            "front": self.front,
            "back": self.back,
            "difficulty": self.difficulty,
            "review_count": self.review_count,
            "last_reviewed_at": self.last_reviewed_at.isoformat()
            if self.last_reviewed_at
            else None,
            "created_at": self.created_at.isoformat(),
        }
