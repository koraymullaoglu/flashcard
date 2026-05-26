import factory
from faker import Faker

from models import Deck, Flashcard

fake = Faker("tr_TR")


class DeckFactory(factory.Factory):
    class Meta:
        model = Deck

    name = factory.LazyFunction(lambda: f"{fake.word()}-{fake.uuid4()[:8]}")
    description = factory.LazyFunction(fake.sentence)
    user_id = 1


class FlashcardFactory(factory.Factory):
    class Meta:
        model = Flashcard

    front = factory.LazyFunction(lambda: f"Soru: {fake.sentence()}")
    back = factory.LazyFunction(lambda: f"Cevap: {fake.sentence()}")
