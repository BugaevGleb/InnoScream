from datetime import datetime

from app.core.schemas import (
    UserMessage,
    Reaction,
    ReactionUpdate,
    ReactionResponse,
)


def test_user_message_schema():
    """Test instantiation of UserMessage schema."""
    now = datetime.utcnow()
    data = {
        "message_id": 1,
        "user_id": "abc123",
        "message": "Test message",
        "created_at": now,
    }

    schema = UserMessage(**data)

    assert schema.message_id == 1
    assert schema.user_id == "abc123"
    assert schema.message == "Test message"
    assert schema.created_at == now


def test_reaction_schema():
    """Test instantiation of Reaction schema."""
    data = {"type": "🔥", "total_count": 5}
    schema = Reaction(**data)

    assert schema.type == "🔥"
    assert schema.total_count == 5


def test_reaction_update_schema():
    """Test instantiation of ReactionUpdate schema."""
    now = datetime.utcnow()
    data = {
        "message_id": 10,
        "changed_at": now,
        "reactions": [{"type": "😂", "total_count": 2}],
    }

    schema = ReactionUpdate(**data)

    assert schema.message_id == 10
    assert schema.changed_at == now
    assert len(schema.reactions) == 1
    assert schema.reactions[0].type == "😂"
    assert schema.reactions[0].total_count == 2


def test_reaction_response_schema():
    """Test instantiation of ReactionResponse schema."""
    now = datetime.utcnow()
    data = {
        "message_id": 42,
        "changed_at": now,
        "reactions": [Reaction(type="💯", total_count=1)],
    }

    schema = ReactionResponse(**data)

    assert schema.message_id == 42
    assert schema.changed_at == now
    assert len(schema.reactions) == 1
    assert schema.reactions[0].type == "💯"
    assert schema.reactions[0].total_count == 1
