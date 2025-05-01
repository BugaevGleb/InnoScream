from unittest import mock
from unittest.mock import MagicMock
import io
import os

import pytest
from PIL import Image, ImageDraw, ImageFont

from app.bot import meme_generator as mg


def test_extract_keywords():
    """Test extract_keywords returns correct list of keywords."""
    assert mg.extract_keywords("funny cats") == ["funny", "cats"]


def test_get_text_size_bbox(monkeypatch):
    """Test get_text_size returns correct dimensions and applies the font."""
    image = Image.new("RGB", (200, 100))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    called = {}

    def fake_textbbox(pos, text_arg, **kwargs):
        called['pos'] = pos
        called['text'] = text_arg
        called['font'] = kwargs.get('font')
        return (1, 2, 16, 27)

    monkeypatch.setattr(draw, "textbbox", fake_textbbox)

    width, height = mg.get_text_size(draw, "hello", font)

    assert width == 15  # 16 - 1
    assert height == 25  # 27 - 2

    assert called['pos'] == (0, 0)
    assert called['text'] == "hello"
    assert called['font'] is font


def test_get_text_size_bbox_fallback(monkeypatch):
    """Test get_text_size returns correct dimensions and applies the font."""
    image = Image.new("RGB", (200, 100))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    called = {}

    def fake_textbbox(pos, text_arg, **kwargs):
        raise AttributeError("no bbox")

    def fake_textlength(text_arg, **kwargs):
        called['text'] = text_arg
        called['font'] = kwargs.get('font')
        return 42.7

    monkeypatch.setattr(draw, "textbbox", fake_textbbox)
    monkeypatch.setattr(draw, "textlength", fake_textlength)

    width, height = mg.get_text_size(draw, "fallback", font)

    assert width == 42
    assert height == 10

    assert called['text'] == "fallback"
    assert called['font'] is font


def test_get_text_size_double_fallback_returns_zero(monkeypatch):
    """
    If both textbbox and textlength are missing,
    get_text_size returns (0,0)
    """
    class BareDraw:
        def textbbox(self, *args, **kwargs):
            raise AttributeError

        def textlength(self, *args, **kwargs):
            raise AttributeError

    w, h = mg.get_text_size(BareDraw(), "anything", ImageFont.load_default())
    assert (w, h) == (0, 0)


@pytest.mark.parametrize(
    "text,max_width,expected",
    [
        ("", 100, []),
        ("single", 100, ["single"]),
        ("a b c", 100, ["a b c"]),
        ("one two three", 100, ["one two", "three"]),
        ("x y z w v u", 30, ["x y", "z w", "v u"]),
    ],
)
def test_wrap_text_pixel_various(monkeypatch, text, max_width, expected):
    """Test wrap_text_pixel behavior and ensure no line exceeds max_width."""
    called = {}

    class FakeDraw:
        def textbbox(self, pos, txt, font):
            # record calls
            called.setdefault("calls", []).append((pos, txt, font))
            # width in pixels = len(txt) * 10
            return (0, 0, len(txt) * 10, 0)

    draw = FakeDraw()
    font = ImageFont.load_default()
    result = mg.wrap_text_pixel(text, font, draw, max_width)

    # check wrapped lines match expectation
    assert result == expected

    # verify first call parameters
    if called.get("calls"):
        pos, txt, fnt = called["calls"][0]
        assert pos == (0, 0)
        assert fnt is font
        if text and " " in text:
            first_word = text.split()[0]
            assert txt.startswith(first_word)

    # ensure each output line width <= max_width
    for line in result:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        assert line_width <= max_width, (
            f"Line '{line}' width {line_width} exceeds {max_width}"
        )


def test_memory_file_read():
    """Test MemoryFile read returns the initialized bytes."""
    mf = mg.MemoryFile(b"hello")
    assert mf.read() == b"hello"


def test_get_text_size_fallback(monkeypatch):
    """Test get_text_size uses fallback when textbbox is missing."""
    image = Image.new("RGB", (200, 100))
    draw = ImageDraw.Draw(image)
    monkeypatch.setattr(
        draw,
        "textbbox",
        lambda pos, text, font: (_ for _ in ()).throw(
            AttributeError("No textbbox")
        ),
    )

    def mock_textlength(text, font):
        return 50

    monkeypatch.setattr(draw, "textlength", mock_textlength)
    font = ImageFont.load_default()
    width, height = mg.get_text_size(draw, "test", font)
    assert width == 50
    assert height == font.size


def test_calculate_font_size_basic(monkeypatch):
    """Test calculate_font_size returns valid font size."""
    draw = ImageDraw.Draw(Image.new("RGB", (300, 300)))
    font_path = mg.get_font_path()
    result = mg.calculate_font_size("short text", font_path, draw, 250, 300)
    assert isinstance(result, int)
    assert result > 0


def test_calculate_font_size_none(monkeypatch):
    """Test calculate_font_size returns 10 when font_path is None."""
    draw = ImageDraw.Draw(Image.new("RGB", (300, 300)))
    result = mg.calculate_font_size("anything", None, draw, 250, 300)
    assert result == 10


def test_calculate_font_size_ioerror(monkeypatch):
    """Test calculate_font_size returns 1 on persistent IOError."""
    draw = ImageDraw.Draw(Image.new("RGB", (300, 300)))
    monkeypatch.setattr(
        ImageFont,
        "truetype",
        lambda path, size: (_ for _ in ()).throw(IOError("fail")),
    )
    result = mg.calculate_font_size("text", "dummy_path", draw, 250, 300)
    assert result == 1


def test_get_font_path_valid(monkeypatch):
    """Test get_font_path returns valid path or None."""
    path = mg.get_font_path()
    if path:
        assert path.lower().endswith(".ttf")
    else:
        assert path is None


def test_get_font_path_failure(monkeypatch):
    """Test get_font_path returns None when font loading fails."""
    monkeypatch.setattr(os.path, "exists", lambda path: True)

    def mock_truetype(path, size):
        return (_ for _ in ()).throw(IOError("fail"))

    monkeypatch.setattr(ImageFont, "truetype", mock_truetype)
    result = mg.get_font_path()
    assert result is None


def test_draw_text_runs(monkeypatch):
    """
    Test draw_text executes without raising exceptions
    and calls draw.text correctly
    """
    img = Image.new("RGBA", (500, 300))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    lines = ["hello", "world"]
    heights = [10, 10]
    line_spacing = 2
    stroke_width = 1

    monkeypatch.setattr(mg, "get_text_size", lambda d, txt, f: (100, 10))

    # wrap draw.text with MagicMock to capture calls
    orig_text = draw.text
    mock_draw_text = MagicMock(wraps=orig_text)
    draw.text = mock_draw_text

    mg.draw_text(draw, lines, font, heights,
                 line_spacing, 500, 0, stroke_width)

    assert mock_draw_text.call_count == 2
    base_x = (500 - 100) / 2
    expected_positions = [(base_x, 0), (base_x, heights[0] + line_spacing)]
    for idx, call in enumerate(mock_draw_text.call_args_list):
        args, kwargs = call
        assert args[0] == expected_positions[idx]
        assert args[1] == lines[idx]
        assert kwargs["font"] is font
        assert kwargs["fill"] == "white"
        assert kwargs["stroke_width"] == stroke_width
        assert kwargs["stroke_fill"] == "black"


def test_draw_text_typeerror_call_count(monkeypatch):
    """Test draw_text makes correct number of calls when using fallback."""
    monkeypatch.setattr(mg, "get_text_size", lambda d, txt, f: (80, 10))

    class DummyDraw:
        def __init__(self):
            self.calls = []

        def text(self, pos, text, font, fill, **kwargs):
            if "stroke_width" in kwargs:
                raise TypeError("Simulated stroke failure")
            self.calls.append((pos, text, fill))

    dummy = DummyDraw()
    font = ImageFont.load_default()
    lines = ["line1", "line2"]
    text_heights = [10, 10]

    mg.draw_text(dummy, lines, font, text_heights, 2, 500, 0, 5)

    # each line => 8 outline calls + 1 main text = 9, total 18
    assert len(dummy.calls) == 9 * len(lines)


def test_draw_text_typeerror_first_line_positions(monkeypatch):
    """Test draw_text positions for first line outline calls."""
    monkeypatch.setattr(mg, "get_text_size", lambda d, txt, f: (80, 10))

    class DummyDraw:
        def __init__(self):
            self.calls = []

        def text(self, pos, text, font, fill, **kwargs):
            if "stroke_width" in kwargs:
                raise TypeError("Simulated stroke failure")
            self.calls.append((pos, text, fill))

    dummy = DummyDraw()
    font = ImageFont.load_default()
    lines = ["line1", "line2"]
    text_heights = [10, 10]
    spacing = 2
    width = 500
    y_start = 0
    stroke_w = 5

    mg.draw_text(dummy, lines, font, text_heights,
                 spacing, width, y_start, stroke_w)

    base_x = (width - 80) / 2
    offsets = [
        (-stroke_w, -stroke_w),
        (-stroke_w, stroke_w),
        (stroke_w, -stroke_w),
        (stroke_w, stroke_w),
        (-stroke_w, 0),
        (stroke_w, 0),
        (0, -stroke_w),
        (0, stroke_w),
    ]

    # Check outline positions for first line
    for i, (dx, dy) in enumerate(offsets):
        pos, txt, fill = dummy.calls[i]
        assert txt == lines[0]
        assert fill == "black"
        assert pos == (base_x + dx, y_start + dy)


def test_draw_text_typeerror_first_line_main_text(monkeypatch):
    """Test draw_text main text position for first line."""
    monkeypatch.setattr(mg, "get_text_size", lambda d, txt, f: (80, 10))

    class DummyDraw:
        def __init__(self):
            self.calls = []

        def text(self, pos, text, font, fill, **kwargs):
            if "stroke_width" in kwargs:
                raise TypeError("Simulated stroke failure")
            self.calls.append((pos, text, fill))

    dummy = DummyDraw()
    font = ImageFont.load_default()
    lines = ["line1", "line2"]
    text_heights = [10, 10]

    mg.draw_text(dummy, lines, font, text_heights, 2, 500, 0, 5)

    # Check main text for first line
    pos, txt, fill = dummy.calls[8]
    assert txt == lines[0]
    assert fill == "white"
    assert pos == ((500 - 80) / 2, 0)


def test_draw_text_typeerror_second_line_positions(monkeypatch):
    """Test draw_text positions for second line outline calls."""
    monkeypatch.setattr(mg, "get_text_size", lambda d, txt, f: (80, 10))

    class DummyDraw:
        def __init__(self):
            self.calls = []

        def text(self, pos, text, font, fill, **kwargs):
            if "stroke_width" in kwargs:
                raise TypeError("Simulated stroke failure")
            self.calls.append((pos, text, fill))

    dummy = DummyDraw()
    font = ImageFont.load_default()
    lines = ["line1", "line2"]
    text_heights = [10, 10]
    spacing = 2
    width = 500
    y_start = 0
    stroke_w = 5

    mg.draw_text(dummy, lines, font, text_heights,
                 spacing, width, y_start, stroke_w)

    base_x = (width - 80) / 2
    offsets = [
        (-stroke_w, -stroke_w),
        (-stroke_w, stroke_w),
        (stroke_w, -stroke_w),
        (stroke_w, stroke_w),
        (-stroke_w, 0),
        (stroke_w, 0),
        (0, -stroke_w),
        (0, stroke_w),
    ]

    y1 = y_start + text_heights[0] + spacing
    start2 = 9

    # Check outline positions for second line
    for i, (dx, dy) in enumerate(offsets):
        pos, txt, fill = dummy.calls[start2 + i]
        assert txt == lines[1]
        assert fill == "black"
        assert pos == (base_x + dx, y1 + dy)


def test_draw_text_typeerror_second_line_main_text(monkeypatch):
    """Test draw_text main text position for second line."""
    monkeypatch.setattr(mg, "get_text_size", lambda d, txt, f: (80, 10))

    class DummyDraw:
        def __init__(self):
            self.calls = []

        def text(self, pos, text, font, fill, **kwargs):
            if "stroke_width" in kwargs:
                raise TypeError("Simulated stroke failure")
            self.calls.append((pos, text, fill))

    dummy = DummyDraw()
    font = ImageFont.load_default()
    lines = ["line1", "line2"]
    text_heights = [10, 10]
    spacing = 2
    width = 500
    y_start = 0

    mg.draw_text(dummy, lines, font, text_heights, spacing, width, y_start, 5)

    y1 = y_start + text_heights[0] + spacing

    # Check main text for second line
    pos, txt, fill = dummy.calls[17]
    assert txt == lines[1]
    assert fill == "white"
    assert pos == ((width - 80) / 2, y1)


def test_fetch_background_image_success(monkeypatch):
    """
    Test fetch_background_image returns Image on successful
    request and calls correct URL.
    """
    import io
    from PIL import Image
    from app.bot import meme_generator as mg

    # prepare dummy image bytes
    dummy_img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    dummy_img.save(buf, format="PNG")
    buf.seek(0)
    dummy_img_bytes = buf.getvalue()

    class DummyResponse:
        def raise_for_status(self): pass

        def json(self):
            return {"urls": {"regular": "https://example.com/dummy.png"}}

        @property
        def content(self):
            return dummy_img_bytes

    # capture URLs called
    called_urls = []

    def dummy_get(self, url, *args, **kwargs):
        called_urls.append(url)
        return DummyResponse()

    monkeypatch.setattr(
        mg.httpx,
        "Client",
        lambda timeout: type(
            "Client",
            (object,),
            {
                "__enter__": lambda s: s,
                "__exit__": lambda s, et, ev, tb: None,
                "get": dummy_get,
            },
        )(),
    )

    img = mg.fetch_background_image(["dummy1", "dummy2"], "key")
    assert img is not None
    assert isinstance(img, Image.Image)
    assert img.mode == "RGBA", f"Image mode is {img.mode}, expected RGBA"

    # assert the Unsplash API URL was constructed correctly
    expected_url = (
        "https://api.unsplash.com/photos/random"
        "?query=dummy1+dummy2"
        "&client_id=key"
        "&orientation=landscape"
    )
    assert called_urls, "No URL was requested"
    assert called_urls[0] == expected_url


def test_fetch_background_image_http_error(monkeypatch):
    """Test fetch_background_image returns None on HTTP error."""
    from httpx import HTTPStatusError

    def dummy_get(*args, **kwargs):
        class DummyResponse:
            def raise_for_status(self):
                raise HTTPStatusError("Error", request=None, response=None)

            def json(self):
                return {"urls": {"regular": "dummy"}}

            @property
            def content(self):
                return b"dummy"

        return DummyResponse()

    monkeypatch.setattr(
        mg.httpx,
        "Client",
        lambda timeout: type(
            "Client",
            (object,),
            {
                "__enter__": lambda s: s,
                "__exit__": lambda s, *args: None,
                "get": dummy_get,
            },
        )(),
    )
    img = mg.fetch_background_image(["dummy"], "key")
    assert img is None


def test_fetch_background_image_keyerror(monkeypatch):
    """Test fetch_background_image returns None on missing JSON key."""
    def dummy_get(*args, **kwargs):
        class DummyResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {}

            @property
            def content(self):
                return b"dummy"

        return DummyResponse()

    monkeypatch.setattr(
        mg.httpx,
        "Client",
        lambda timeout: type(
            "Client",
            (object,),
            {
                "__enter__": lambda s: s,
                "__exit__": lambda s, *args: None,
                "get": dummy_get,
            },
        )(),
    )
    img = mg.fetch_background_image(["dummy"], "key")
    assert img is None


@pytest.fixture
def mock_meme_dependencies(monkeypatch):
    """Setup common mocks for meme generator tests."""
    dummy_img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    dummy_img.save(buf, format="PNG")
    buf.seek(0)
    dummy_img_bytes = buf.getvalue()

    class DummyResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"urls": {"regular": "https://example.com/img.jpg"}}

        @property
        def content(self):
            return dummy_img_bytes

    def dummy_get(*args, **kwargs):
        return DummyResponse()

    # Mock key functions
    mocks = {
        "dummy_img": dummy_img,
        "extract_keywords": mock.Mock(return_value=["hello", "meme"]),
        "fetch_bg": mock.Mock(return_value=dummy_img),
        "get_font_path": mock.Mock(return_value=None),
        "calculate_font_size": mock.Mock(return_value=20),
        "wrap_text_pixel": mock.Mock(return_value=["hello meme"]),
        "get_text_size": mock.Mock(return_value=(50, 20)),
        "draw_text": mock.Mock()
    }

    # Set up monkeypatches
    monkeypatch.setattr(mg, "extract_keywords", mocks["extract_keywords"])
    monkeypatch.setattr(mg, "fetch_background_image", mocks["fetch_bg"])
    monkeypatch.setattr(mg, "get_font_path", mocks["get_font_path"])
    monkeypatch.setattr(mg, "calculate_font_size",
                        mocks["calculate_font_size"])
    monkeypatch.setattr(mg, "wrap_text_pixel", mocks["wrap_text_pixel"])
    monkeypatch.setattr(mg, "get_text_size", mocks["get_text_size"])
    monkeypatch.setattr(mg, "draw_text", mocks["draw_text"])

    monkeypatch.setattr(
        mg.httpx,
        "Client",
        lambda timeout: type(
            "Client",
            (object,),
            {
                "__enter__": lambda s: s,
                "__exit__": lambda s, et, ev, tb: None,
                "get": dummy_get,
            },
        )(),
    )

    return mocks


@pytest.mark.parametrize("output_filename", ["out.jpg", "out.png"])
def test_generate_meme_success(
        monkeypatch,
        mock_meme_dependencies,
        output_filename
):
    """
    Test generate_meme returns valid image
    bytes for supported formats
    """

    # Call the function being tested
    meme = mg.generate_meme("hello meme", "fake_api_key", output_filename)

    # Verify result is valid
    assert meme is not None
    meme_bytes = meme.getvalue()
    assert isinstance(meme_bytes, bytes)
    assert len(meme_bytes) > 0


def test_generate_meme_function_calls(mock_meme_dependencies):
    """Test all dependencies are called with correct arguments."""
    mocks = mock_meme_dependencies

    # Call the function being tested
    mg.generate_meme("hello meme", "fake_api_key", "out.jpg")

    # Verify basic function calls
    mocks["extract_keywords"].assert_called_once_with("hello meme")
    mocks["fetch_bg"].assert_called_once_with(
        ["hello", "meme"], "fake_api_key")
    mocks["get_font_path"].assert_called_once()


def test_font_size_calculation_args(mock_meme_dependencies):
    """Test calculate_font_size receives correct arguments."""
    mocks = mock_meme_dependencies

    # Call the function being tested
    mg.generate_meme("hello meme", "fake_api_key", "out.jpg")

    # Check calculate_font_size was called with correct arguments
    _, args, _ = mocks["calculate_font_size"].mock_calls[0]
    assert args[0] == "hello meme"
    assert args[1] is None  # font_path
    assert isinstance(args[2], ImageDraw.ImageDraw)
    assert args[3] == 90  # max_text_width (100 - 2*5)
    assert args[4] == 100  # image_height


def test_text_wrapping_args(mock_meme_dependencies):
    """Test text wrapping gets correct arguments."""
    mocks = mock_meme_dependencies

    # Call the function being tested
    mg.generate_meme("hello meme", "fake_api_key", "out.jpg")

    # Check wrap_text_pixel was called correctly
    mocks["wrap_text_pixel"].assert_called_once()
    wrap_args = mocks["wrap_text_pixel"].call_args[0]
    assert wrap_args[0] == "hello meme"
    assert isinstance(wrap_args[1], ImageFont.FreeTypeFont)
    assert isinstance(wrap_args[2], ImageDraw.ImageDraw)
    assert wrap_args[3] == 90  # max_text_width


def test_draw_text_args(mock_meme_dependencies):
    """Test draw_text is called with correct arguments."""
    mocks = mock_meme_dependencies

    # Call the function being tested
    mg.generate_meme("hello meme", "fake_api_key", "out.jpg")

    # Check draw_text was called with correct arguments
    mocks["draw_text"].assert_called_once()
    args = mocks["draw_text"].call_args[0]
    assert isinstance(args[0], ImageDraw.ImageDraw)  # draw
    assert args[1] == ["hello meme"]  # lines
    assert isinstance(args[2], ImageFont.FreeTypeFont)  # font
    assert args[3] == [20]  # text_heights
    assert args[4] == 2  # line_spacing
    assert args[5] == 100  # image_width
    assert args[6] == 75  # y_start
    assert args[7] == 1  # stroke_width


def test_generate_meme_fail_fetch(monkeypatch):
    """Test generate_meme returns None when background fetch fails."""
    extract_keywords_mock = mock.Mock(return_value=["some", "text"])
    monkeypatch.setattr(mg, "extract_keywords", extract_keywords_mock)

    fetch_bg_mock = mock.Mock(return_value=None)
    monkeypatch.setattr(mg, "fetch_background_image", fetch_bg_mock)

    meme = mg.generate_meme("some text", "any_key")

    extract_keywords_mock.assert_called_once_with("some text")
    fetch_bg_mock.assert_called_once_with(["some", "text"], "any_key")
    assert meme is None


def test_generate_meme_jpeg_conversion(monkeypatch):
    """Test generate_meme converts RGBA to RGB when saving as JPEG."""
    dummy_img = Image.new("RGBA", (100, 100))

    extract_keywords_mock = mock.Mock(return_value=["some", "text"])
    monkeypatch.setattr(mg, "extract_keywords", extract_keywords_mock)

    fetch_bg_mock = mock.Mock(return_value=dummy_img)
    monkeypatch.setattr(mg, "fetch_background_image", fetch_bg_mock)

    get_font_path_mock = mock.Mock(return_value=None)
    monkeypatch.setattr(mg, "get_font_path", get_font_path_mock)

    calculate_font_size_mock = mock.Mock(return_value=20)
    monkeypatch.setattr(mg, "calculate_font_size", calculate_font_size_mock)

    wrap_text_pixel_mock = mock.Mock(return_value=["some text"])
    monkeypatch.setattr(mg, "wrap_text_pixel", wrap_text_pixel_mock)

    get_text_size_mock = mock.Mock(return_value=(50, 20))
    monkeypatch.setattr(mg, "get_text_size", get_text_size_mock)

    draw_text_mock = mock.Mock()
    monkeypatch.setattr(mg, "draw_text", draw_text_mock)

    convert_mock = mock.Mock(return_value=Image.new("RGB", (100, 100)))
    dummy_img.convert = convert_mock

    meme = mg.generate_meme("some text", "any_key", "output.jpg")

    extract_keywords_mock.assert_called_once_with("some text")
    fetch_bg_mock.assert_called_once_with(["some", "text"], "any_key")
    convert_mock.assert_called_once_with("RGB")

    assert meme is not None
    data = meme.getvalue()
    assert isinstance(data, bytes)
    assert len(data) > 0


def test_get_max_theoretical_size():
    """Test that get_max_theoretical_size returns the correct value."""
    assert mg.get_max_theoretical_size(100) == 20
    assert mg.get_max_theoretical_size(500) == 100
    assert mg.get_max_theoretical_size(1000) == 200
    assert mg.get_max_theoretical_size(-5) == -1
    assert mg.get_max_theoretical_size(-4) == -1


def test_get_font_path_success(monkeypatch):
    """Returns path when font exists and loads without error"""
    monkeypatch.setattr(mg.platform, "system", lambda: "Windows")
    monkeypatch.setattr(mg.os.path, "exists", lambda path: True)
    truetype_spy = MagicMock(return_value=True)
    monkeypatch.setattr(mg.ImageFont, "truetype", truetype_spy)

    result = mg.get_font_path()

    assert result == "C:/Windows/Fonts/impact.ttf"
    truetype_spy.assert_called_once_with("C:/Windows/Fonts/impact.ttf", 10)


def test_get_font_path_not_exists(monkeypatch):
    """Returns None when font file does not exist"""
    monkeypatch.setattr(mg.platform, "system", lambda: "Linux")
    monkeypatch.setattr(mg.os.path, "exists", lambda path: False)

    result = mg.get_font_path()
    assert result is None


def test_get_font_path_ioerror(monkeypatch):
    """Returns None when truetype raises IOError"""
    monkeypatch.setattr(mg.platform, "system", lambda: "Linux")
    monkeypatch.setattr(mg.os.path, "exists", lambda path: True)
    monkeypatch.setattr(
        mg.ImageFont, "truetype",
        lambda path, size: (_ for _ in ()).throw(IOError("fail"))
    )

    result = mg.get_font_path()
    assert result is None
