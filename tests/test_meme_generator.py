import io
import os

import pytest
from PIL import Image, ImageDraw, ImageFont

from app.bot import meme_generator as mg


def test_extract_keywords():
    """Test extract_keywords returns correct list of keywords."""
    assert mg.extract_keywords("funny cats") == ["funny", "cats"]


def test_get_text_size_bbox(monkeypatch):
    """Test get_text_size returns positive dimensions using textbbox."""
    image = Image.new("RGB", (200, 100))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    width, height = mg.get_text_size(draw, "hello", font)
    assert width > 0
    assert height > 0


def test_wrap_text_pixel_short_line():
    """Test wrap_text_pixel returns list of strings for short lines."""
    img = Image.new("RGB", (500, 300))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    lines = mg.wrap_text_pixel("a b c d", font, draw, 200)
    assert isinstance(lines, list)
    assert all(isinstance(line, str) for line in lines)


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


def test_draw_text_runs():
    """Test draw_text executes without raising exceptions."""
    img = Image.new("RGBA", (500, 300))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    lines = ["hello", "world"]
    heights = [10, 10]
    mg.draw_text(draw, lines, font, heights, 2, 500, 0, 1)


def test_draw_text_typeerror(monkeypatch):
    """Test draw_text handles stroke TypeError with fallback."""
    class DummyDraw:
        def __init__(self):
            self.calls = []

        def text(self, pos, text, font, fill, **kwargs):
            if "stroke_width" in kwargs:
                raise TypeError("Simulated stroke failure")
            self.calls.append((pos, text, font, fill, kwargs))

    dummy = DummyDraw()
    font = ImageFont.load_default()
    lines = ["line1", "line2"]
    text_heights = [10, 10]
    mg.draw_text(dummy, lines, font, text_heights, 2, 500, 0, 5)
    assert len(dummy.calls) >= 1


def test_fetch_background_image_success(monkeypatch):
    """Test fetch_background_image returns Image on successful request."""
    dummy_img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    dummy_img.save(buf, format="PNG")
    buf.seek(0)
    dummy_img_bytes = buf.getvalue()

    class DummyResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"urls": {"regular": "https://example.com/dummy.png"}}

        @property
        def content(self):
            return dummy_img_bytes

    def dummy_get(*args, **kwargs):
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
    img = mg.fetch_background_image(["dummy"], "key")
    assert img is not None
    assert isinstance(img, Image.Image)


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


@pytest.mark.parametrize("output_filename", ["out.jpg", "out.png"])
def test_generate_meme_success(monkeypatch, output_filename):
    """Test generate_meme returns valid image bytes for supported formats."""
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
    monkeypatch.setattr(mg, "get_font_path", lambda: None)
    meme = mg.generate_meme("hello meme", "fake_api_key", output_filename)
    assert meme is not None
    meme_bytes = meme.getvalue()
    assert isinstance(meme_bytes, bytes)
    assert len(meme_bytes) > 0


def test_generate_meme_fail_fetch(monkeypatch):
    """Test generate_meme returns None when background fetch fails."""
    monkeypatch.setattr(
        mg,
        "fetch_background_image",
        lambda keywords,
        key: None)
    meme = mg.generate_meme("some text", "any_key")
    assert meme is None


def test_generate_meme_jpeg_conversion(monkeypatch):
    """Test generate_meme converts RGBA to RGB when saving as JPEG."""
    dummy_img = Image.new("RGBA", (100, 100))
    monkeypatch.setattr(
        mg,
        "fetch_background_image",
        lambda keywords,
        key: dummy_img)
    monkeypatch.setattr(mg, "get_font_path", lambda: None)
    meme = mg.generate_meme("some text", "any_key", "output.jpg")
    assert meme is not None
    data = meme.getvalue()
    assert isinstance(data, bytes)
    assert len(data) > 0
