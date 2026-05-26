from flask import Blueprint, render_template

from extensions import db
from models import Deck

view_bp = Blueprint("view", __name__)


@view_bp.get("/")
def index():
    """Render the deck listing page."""
    return render_template("index.html")


@view_bp.get("/auth")
def auth():
    """Render the login / register page."""
    return render_template("auth.html")


@view_bp.get("/decks/<int:deck_id>")
def deck_detail(deck_id: int):
    """Render the deck detail / study page."""
    deck = db.session.get(Deck, deck_id)
    if deck is None:
        return render_template("index.html"), 404
    return render_template("deck_detail.html", deck=deck)
