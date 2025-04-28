import requests
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
import platform
import textwrap
import os


def extract_keywords(message_text: str) -> list[str]:
    """Naively splits the message into words (improvement: use NLP)."""
    return message_text.split()


def fetch_background_image(keywords: list[str], unsplash_access_key: str) -> Image.Image | None:
    """
    Fetch a random landscape image from Unsplash based on keywords.
    
    Returns an RGBA image or None on failure.
    """
    query = '+'.join(keywords)
    url = f"https://api.unsplash.com/photos/random?query={query}&client_id={unsplash_access_key}&orientation=landscape"
    print(f"[Debug] Fetching image from: {url}")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        image_url = data['urls']['regular']
        img_response = requests.get(image_url, timeout=15)
        img_response.raise_for_status()
        return Image.open(BytesIO(img_response.content)).convert("RGBA")
    except requests.exceptions.RequestException as e:
        print(f"[Error] Error fetching background image: {e}")
    except KeyError:
        print("[Error] Error parsing Unsplash response (key missing)")
    return None


def get_text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    """
    Returns the bounding box size (width, height) of the given text.
    Uses textbbox; falls back to textlength if needed.
    """
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return (width, height)
    except AttributeError:
        print("[Warning] textbbox not available; attempting fallback.")
        try:
            width = draw.textlength(text, font=font)
            return (width, font.size)
        except AttributeError:
            return (0, 0)


def wrap_text_pixel(text: str, font: ImageFont.FreeTypeFont, draw: ImageDraw.ImageDraw, max_width: int) -> list[str]:
    """
    Wraps the input text to fit within max_width (in pixels) using a simple algorithm.
    Returns a list of string lines.
    """
    lines = []
    words = text.split()
    if not words:
        return lines
    current_line = words[0]
    for word in words[1:]:
        test_line = f"{current_line} {word}"
        bbox = draw.textbbox((0,0), test_line, font=font)
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
        return super().read(*args, **kwargs)


def generate_meme(message_text: str, unsplash_access_key: str, output_filename: str = "generated_meme.jpg", size_coefficient: float = 1/1.5) -> MemoryFile | None:
    """
    Generates a meme image by overlaying message_text onto a background image fetched from Unsplash.
    The size_coefficient is applied to the optimal font size.
    
    Instead of saving to disk, this version returns a MemoryFile (a BytesIO subclass) containing the image.
    Returns the MemoryFile on success, or None on failure.
    """
    keywords = extract_keywords(message_text)
    print(f"[Debug] Keywords for image search: {keywords}")

    bg_image = fetch_background_image(keywords, unsplash_access_key)
    if bg_image is None:
        print("[Error] Failed to get background image. Aborting meme generation.")
        return None

    image_width, image_height = bg_image.size
    print(f"[Debug] Image dimensions: Width={image_width}, Height={image_height}")
    draw = ImageDraw.Draw(bg_image)

    margin = int(image_width * 0.05)
    max_text_width = image_width - 2 * margin
    print(f"[Debug] Margin={margin}, Max text width={max_text_width}")

    font_path = None
    try:
        if platform.system() == "Windows":
            test_path = "C:/Windows/Fonts/impact.ttf"
        else:
            test_path = "Impact.ttf"
        print(f"[Debug] Checking font path: {test_path}")
        if os.path.exists(test_path):
            _ = ImageFont.truetype(test_path, 10)
            font_path = test_path
            print(f"[Info] Found font: {font_path}")
        else:
            print("[Warning] Font file not found. Will use default font.")
    except IOError as e:
        print(f"[Warning] IOError loading font '{test_path}': {e}")
    
    if font_path is None:
        print("[Info] Using Pillow's default font.")

    optimal_font_size = 1
    max_theoretical_size = int(min(image_height / 4, image_width / 5))
    print(f"[Debug] Max theoretical font size to check: {max_theoretical_size}")

    if font_path:
        for size in range(10, max_theoretical_size, 2):
            try:
                font_candidate = ImageFont.truetype(font_path, size)
            except IOError:
                print(f"[Debug] Skipping font size {size} due to IOError.")
                continue

            lines_candidate = wrap_text_pixel(message_text, font_candidate, draw, max_text_width)
            text_heights = [get_text_size(draw, line, font_candidate)[1] for line in lines_candidate]
            line_spacing_candidate = int(size * 0.2)
            total_text_height_candidate = sum(text_heights) + line_spacing_candidate * max(0, len(lines_candidate) - 1)
            vertical_fit_limit = image_height * 0.6

            if total_text_height_candidate < vertical_fit_limit:
                optimal_font_size = size
            else:
                break
    else:
        optimal_font_size = 10
        print("[Debug] Default font used; optimal font size set to 10.")

    print(f"[Result] Optimal font size (max fit): {optimal_font_size}")

    final_font_size = max(1, int(optimal_font_size * size_coefficient))
    print(f"[Result] Final font size after applying coefficient {size_coefficient:.2f}: {final_font_size}")

    try:
        if font_path:
            font = ImageFont.truetype(font_path, final_font_size)
            print(f"[Debug] Loaded font {font_path} at size {final_font_size}.")
        else:
            font = ImageFont.load_default()
            final_font_size = 10
            print("[Info] Using default font; final font size set to 10.")
    except IOError as e:
        print(f"[Error] Failed to load font {font_path} at size {final_font_size}: {e}. Using default.")
        font = ImageFont.load_default()
        final_font_size = 10
    
    line_spacing = int(final_font_size * 0.2)
    stroke_width = max(1, final_font_size // 25)
    print(f"[Debug] Final line spacing: {line_spacing}, stroke width: {stroke_width}")

    print("[Debug] Wrapping text with final font...")
    lines = wrap_text_pixel(message_text, font, draw, max_text_width)
    print(f"[Debug] Wrapped lines: {lines}")

    text_heights = [get_text_size(draw, line, font)[1] for line in lines]
    total_text_height = sum(text_heights) + line_spacing * max(0, len(lines) - 1)
    y_start = image_height - total_text_height - margin
    print(f"[Debug] Text block height: {total_text_height}, Y-start: {y_start}")

    print("[Debug] Drawing text on image...")
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
                stroke_fill=outline_color
            )
        except TypeError:
            offsets = [(-stroke_width, -stroke_width), (-stroke_width, stroke_width),
                       (stroke_width, -stroke_width), (stroke_width, stroke_width),
                       (-stroke_width, 0), (stroke_width, 0), (0, -stroke_width), (0, stroke_width)]
            for dx, dy in offsets:
                draw.text((x_text + dx, current_y + dy), line, font=font, fill=outline_color)
            draw.text((x_text, current_y), line, font=font, fill=text_color)

        current_y += line_height + line_spacing

    output_format = "JPEG" if output_filename.lower().endswith((".jpg", ".jpeg")) else "PNG"
    if output_format == "JPEG":
        print("[Debug] Converting image to RGB for JPEG saving.")
        bg_image = bg_image.convert("RGB")
    
    buffer = BytesIO()
    try:
        bg_image.save(buffer, format=output_format)
        buffer.seek(0)
        print(f"[Success] Meme generated and stored in memory as {output_format}.")
        return MemoryFile(buffer.getvalue())
    except Exception as e:
        print(f"[Error] Failed to save image to memory: {e}")
        return None
