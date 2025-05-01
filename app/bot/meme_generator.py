import logging
import os
import platform
from io import BytesIO

import httpx
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def extract_keywords(message_text: str) -> list[str]:
    """Naively splits the message into words (improvement: use NLP)."""
    return message_text.split()


def fetch_background_image(
    keywords: list[str], unsplash_access_key: str
) -> Image.Image | None:
    """Fetch a random landscape image from Unsplash based on keywords."""
    query = "+".join(keywords)
    url = (
        f"https://api.unsplash.com/photos/random?query={query}"
        f"&client_id={unsplash_access_key}&orientation=landscape"
    )
    logger.info("Fetching image from: %s", url)  # pragma: no mutate
    try:
        with httpx.Client(timeout=15) as client:  # pragma: no mutate
            response = client.get(url)  # pragma: no mutate
            response.raise_for_status()
            img_response = client.get(response.json()["urls"]["regular"])
            img_response.raise_for_status()
        return Image.open(BytesIO(img_response.content)).convert("RGBA")
    except (httpx.HTTPStatusError, httpx.TimeoutException) as e:
        logger.exception("Error fetching background image: %s",
                         e)  # pragma: no mutate
    except KeyError:
        logger.exception(
            "Error parsing Unsplash "
            "response (key missing)")  # pragma: no mutate
    return None


def get_text_size(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> tuple[int, int]:
    """Returns the bounding box size (width, height) of the given text."""
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        width = int(bbox[2] - bbox[0])
        height = int(bbox[3] - bbox[1])
        return width, height
    except AttributeError:
        logger.warning(
            "Textbbox not available; "
            "attempting fallback.")  # pragma: no mutate
        try:
            width = draw.textlength(text, font=font)
            return int(width), int(font.size)  # type: ignore
        except AttributeError:
            return 0, 0


def wrap_text_pixel(
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    draw: ImageDraw.ImageDraw,
    max_width: int,
) -> list[str]:
    """Wraps the input text to fit within max_width (in pixels)."""
    lines = []
    words = text.split()
    if not words:
        return lines
    current_line = words[0]
    for word in words[1:]:
        test_line = f"{current_line} {word}"
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]
        if line_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines


class MemoryFile(BytesIO):
    def read(self, *args, **kwargs):
        """Read bytes from MemoryFile."""
        return super().read(*args, **kwargs)  # pragma: no mutate


def calculate_font_size(
    message_text: str,
    font_path: str | None,
    draw: ImageDraw.ImageDraw,
    max_text_width: int,
    image_height: int,
) -> int:
    """Calculate optimal font size based on available space."""
    optimal_font_size = 1
    max_theoretical_size = get_max_theoretical_size(image_height)
    logger.info("Max theoretical font size: %s",
                max_theoretical_size)  # pragma: no mutate

    if not font_path:
        return 10

    for size in range(10, max_theoretical_size, 2):
        try:
            font_candidate = ImageFont.truetype(font_path, size)
        except IOError:
            logger.info("Skipping font size %s due to IOError",
                        size)  # pragma: no mutate
            continue

        lines_candidate = wrap_text_pixel(  # pragma: no mutate
            message_text, font_candidate,  # pragma: no mutate
            draw, max_text_width  # pragma: no mutate
        )
        text_heights = [
            get_text_size(draw, line, font_candidate)[1]  # pragma: no mutate
            for line in lines_candidate
        ]
        line_spacing = int(size * 0.2)
        tmp = line_spacing * (len(lines_candidate) - 1)
        total_height = sum(text_heights) + tmp
        if total_height < image_height * 0.6:
            optimal_font_size = size
        else:
            break
    return optimal_font_size


def get_max_theoretical_size(image_height: int) -> int:
    """Calculate the maximum theoretical font size based on image height."""
    return int(min(image_height / 4, image_height / 5))


def get_font_path() -> str | None:
    """Determine the appropriate font path for the system."""
    if platform.system() == "Windows":
        test_path = "C:/Windows/Fonts/impact.ttf"
    else:
        test_path = "Impact.ttf"  # pragma: no mutate

    logger.info("Checking font path: %s", test_path)  # pragma: no mutate
    if os.path.exists(test_path):
        try:
            ImageFont.truetype(test_path, 10)
            return test_path
        except IOError as e:
            logger.warning("IOError loading font"
                           "'%s': %s",  # pragma: no mutate
                           test_path, e)  # pragma: no mutate
    return None


def draw_text(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    text_heights: list[int],
    line_spacing: int,
    image_width: int,
    y_start: int,
    stroke_width: int,
) -> None:
    """Draw text on image with proper positioning and stroke effect."""
    outline_color = "black"
    text_color = "white"
    current_y = y_start

    for line, line_height in zip(lines, text_heights):
        line_width = get_text_size(draw, line, font)[0]
        x_text = (image_width - line_width) / 2

        try:
            draw.text(
                (x_text, current_y),
                line,
                font=font,
                fill=text_color,
                stroke_width=stroke_width,
                stroke_fill=outline_color,
            )
        except TypeError:
            offsets = [
                (-stroke_width, -stroke_width),
                (-stroke_width, stroke_width),
                (stroke_width, -stroke_width),
                (stroke_width, stroke_width),
                (-stroke_width, 0),
                (stroke_width, 0),
                (0, -stroke_width),
                (0, stroke_width),
            ]
            for dx, dy in offsets:
                draw.text(
                    (x_text + dx, current_y + dy),
                    line,
                    font=font,
                    fill=outline_color,
                )
            draw.text((x_text, current_y), line, font=font, fill=text_color)

        current_y += line_height + line_spacing


def generate_meme(
    message_text: str,
    unsplash_access_key: str,
    output_filename: str = "generated_meme.jpg",
    size_coefficient: float = 1 / 1.5,
) -> MemoryFile | None:
    """Generates a meme image by overlaying message_text onto an image."""
    keywords = extract_keywords(message_text)
    logger.info("Keywords for image search: %s", keywords)  # pragma: no mutate

    bg_image = fetch_background_image(keywords, unsplash_access_key)
    if bg_image is None:
        logger.error("Failed to get background image.")  # pragma: no mutate
        return None

    image_width, image_height = bg_image.size
    logger.info("Image dimensions: %sx%s", image_width,  # pragma: no mutate
                image_height)  # pragma: no mutate
    draw = ImageDraw.Draw(bg_image)

    margin = int(image_width * 0.05)
    max_text_width = image_width - 2 * margin
    logger.info("Margin: %s, Max text width: %s", margin,  # pragma: no mutate
                max_text_width)  # pragma: no mutate

    font_path = get_font_path()
    if font_path:
        logger.info("Using font: %s", font_path)  # pragma: no mutate
    else:
        logger.info("Using Pillow's default font.")  # pragma: no mutate

    optimal_size = calculate_font_size(
        message_text, font_path, draw, max_text_width, image_height
    )
    logger.info("Optimal font size: %s", optimal_size)  # pragma: no mutate

    final_font_size = max(1, int(optimal_size * size_coefficient))
    logger.info("Final font size: %s", final_font_size)  # pragma: no mutate

    try:
        font = (
            ImageFont.truetype(font_path, final_font_size)
            if font_path
            else ImageFont.load_default()
        )
    except IOError as e:
        font = ImageFont.load_default()
        logger.exception(
            "Failed to load font: %s. Using default.", e)  # pragma: no mutate
        final_font_size = 10  # pragma: no mutate

    line_spacing = int(final_font_size * 0.2)
    stroke_width = max(1, final_font_size // 25)
    logger.info("Line space: %s, Stroke width: %s",  # pragma: no mutate
                line_spacing, stroke_width)  # pragma: no mutate

    logger.info("Wrapping text...")  # pragma: no mutate
    lines = wrap_text_pixel(message_text, font, draw, max_text_width)
    logger.info("Wrapped lines: %s", lines)  # pragma: no mutate

    text_heights = [get_text_size(draw, line, font)[1] for line in lines]
    total_text_height = sum(text_heights) + line_spacing * (len(lines) - 1)
    y_start = image_height - total_text_height - margin
    logger.info("Text height: %s, Y-start: %s",  # pragma: no mutate
                total_text_height, y_start)  # pragma: no mutate

    logger.info("Drawing text...")  # pragma: no mutate
    draw_text(
        draw,
        lines,
        font,
        text_heights,
        line_spacing,
        image_width,
        y_start,
        stroke_width,
    )

    if output_filename.lower().endswith((".jpg", ".jpeg")):
        output_format = "JPEG"
    else:
        output_format = "PNG"
    if output_format == "JPEG":
        logger.info("Converting to RGB for JPEG")  # pragma: no mutate
        bg_image = bg_image.convert("RGB")

    buffer = BytesIO()
    try:
        bg_image.save(buffer, format=output_format)
        buffer.seek(0)
        logger.info("Meme generated as %s", output_format)  # pragma: no mutate
        return MemoryFile(buffer.getvalue())
    except Exception as e:
        logger.exception("Failed to save image: %s", e)  # pragma: no mutate
        return None
