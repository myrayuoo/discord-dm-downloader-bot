import validators
from io import BytesIO
from requests import get
from colorthief import ColorThief

def emoji_to_twemoji_url(emoji: str):
    base = f'{ord(emoji):X}'.lower()
    url = f'https://twemoji.maxcdn.com/v/14.0.2/72x72/{base}.png'
    return url

def get_dominant_color_from_url(image_url):
    if not validators.url(image_url):
        return None
        
    response = get(image_url)

    if not response.ok:
        return None

    color_thief = ColorThief(BytesIO(response.content))
    hex_color = rgb_to_hex(color_thief.get_color(1))

    return int(hex_color[2:], 16)


def rgb_to_hex(rgb):
    return hex((rgb[0] << 16) | (rgb[1] << 8) | (rgb[2] << 0))
