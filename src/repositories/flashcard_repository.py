from sqlalchemy.orm import Session

from models import Flashcard


class FlashcardRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, flashcard_id: int) -> Flashcard | None:
        return self.session.get(Flashcard, flashcard_id)

    def create(self, deck_id: int, front: str, back: str) -> Flashcard:
        flashcard = Flashcard(deck_id=deck_id, front=front, back=back)
        self.session.add(flashcard)
        self.session.commit()
        return flashcard

    def save(self, flashcard: Flashcard) -> Flashcard:
        self.session.add(flashcard)
        self.session.commit()
        return flashcard

    def delete(self, flashcard: Flashcard) -> None:
        self.session.delete(flashcard)
        self.session.commit()
