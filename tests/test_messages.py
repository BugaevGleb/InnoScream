from app.bot import messages as m


def test_start_message():
    """Test START_MESSAGE constant."""
    expected = ("Hello! I'm the InnoScream bot.\n"
                "Use /scream to send a message to the channel.\n"
                "Use /stats to get your stats.\n")
    assert m.START_MESSAGE == expected


def test_admin_start_message():
    """Test ADMIN_START_MESSAGE constant."""
    expected = ("Hello! I'm the InnoScream bot.\n"
                "Use /scream to send a message to the channel.\n"
                "Use /stats to get your stats.\n"
                "Use /pin to pin the best message of the day.\n"
                "Use /generate_meme to generate a meme from the best "
                "message of the day.\n")
    assert m.ADMIN_START_MESSAGE == expected


def test_invalid_text():
    """Test INVALID_TEXT constant."""
    expected = ("Please provide some text after the /scream command. "
                "Usage: `/scream <your text>`")
    assert m.INVALID_TEXT == expected


def test_success_message():
    """Test SUCCESS_MESSAGE constant."""
    assert m.SUCCESS_MESSAGE == "Scream sent to the channel!"


def test_error_message():
    """Test ERROR_MESSAGE constant."""
    assert m.ERROR_MESSAGE == "Could not send message to the channel :("


def test_pin_message():
    """Test PIN_MESSAGE constant."""
    assert m.PIN_MESSAGE == "Pinning best message..."


def test_meme_message():
    """Test MEME_MESSAGE constant."""
    assert m.MEME_MESSAGE == "Generating meme from best message..."


def test_stats_message():
    """Test STATS_MESSAGE formatting."""
    count = 42
    expected = f"You have screamed {count} times into the void."
    assert m.STATS_MESSAGE.format(count=count) == expected
