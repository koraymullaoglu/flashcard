from sqlalchemy.orm import Session

from models import Deck


class DeckRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[Deck]:
        return list(self.session.query(Deck).order_by(Deck.id.desc()).all())

    def get(self, deck_id: int) -> Deck | None:
        return self.session.get(Deck, deck_id)

    def get_by_name(self, name: str) -> Deck | None:
        return self.session.query(Deck).filter(Deck.name == name).one_or_none()

    def create(self, name: str, description: str | None = None) -> Deck:
        deck = Deck(name=name, description=description)
        self.session.add(deck)
        self.session.commit()
        return deck
