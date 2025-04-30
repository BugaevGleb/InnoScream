from datetime import datetime

from app.core.models import UserMessage, Reaction


def test_user_message_model():
    """Test instantiation and repr of UserMessage model."""
    now = datetime.utcnow()
    model = UserMessage(
        message_id=1,
        user_id="abc123",
        message="Hello, world!",
        created_at=now,
    )

    assert model.message_id == 1
    assert model.user_id == "abc123"
    assert model.message == "Hello, world!"
    assert model.created_at == now

    expected_repr = (
        f"<UserMessage(message_id=1, user_id=abc123, created_at={now})>"
    )
    assert repr(model) == expected_repr


def test_reaction_model():
    """Test instantiation and repr of Reaction model."""
    now = datetime.utcnow()
    data = [{"type": "❤️", "total_count": 3}]
    model = Reaction(
        message_id=99,
        changed_at=now,
        reactions=data,
    )

    assert model.message_id == 99
    assert model.changed_at == now
    assert model.reactions == data

    expected_repr = (
        f"<Reaction(message_id=99, changed_at={now}, "
        f"reactions={data})>"
    )
    assert repr(model) == expected_repr
