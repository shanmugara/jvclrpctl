"""
Full-screen HDR/SDR banner renderer for a Linux framebuffer (TFT LCD).
Writes directly to /dev/fb1 (or configurable device) without touching the TTY.
"""

import struct
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

FB_DEVICE = "/dev/fb1"
FB_WIDTH = 480
FB_HEIGHT = 320

_FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

_PALETTE = {
    "HDR": {"bg": (15, 8, 0),  "fg": (255, 140, 0), "sub": (180, 90, 0)},
    "SDR": {"bg": (0, 15, 5),  "fg": (0, 220, 80),  "sub": (0, 150, 50)},
}


def _read_bpp(fb_device: str) -> int:
    name = Path(fb_device).name
    sysfs = Path(f"/sys/class/graphics/{name}/bits_per_pixel")
    try:
        return int(sysfs.read_text().strip())
    except Exception:
        return 16


def _to_fb_bytes(img: Image.Image, bpp: int) -> bytes:
    if bpp == 16:
        try:
            import numpy as np
            arr = np.array(img, dtype=np.uint16)
            rgb565 = ((arr[:, :, 0] >> 3) << 11) | ((arr[:, :, 1] >> 2) << 5) | (arr[:, :, 2] >> 3)
            return rgb565.astype("<u2").tobytes()
        except ImportError:
            buf = bytearray(img.width * img.height * 2)
            pixels = img.load()
            idx = 0
            for y in range(img.height):
                for x in range(img.width):
                    r, g, b = pixels[x, y]
                    struct.pack_into("<H", buf, idx, ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3))
                    idx += 2
            return bytes(buf)
    else:
        # 32-bit BGRA (ARGB8888 little-endian, common for HDMI/some displays)
        r, g, b = img.split()
        alpha = Image.new("L", img.size, 255)
        return Image.merge("RGBA", (b, g, r, alpha)).tobytes()


class TFTBanner:
    """Renders full-screen mode banners to a Linux framebuffer device."""

    def __init__(self, fb_device: str = FB_DEVICE, width: int = FB_WIDTH, height: int = FB_HEIGHT):
        self.fb_device = fb_device
        self.width = width
        self.height = height
        self._bpp: Optional[int] = None

    def show(self, mode: str):
        """Render banner for 'HDR' or 'SDR'. Silently no-ops on any failure."""
        if not _PIL_AVAILABLE:
            return
        try:
            self._render(mode.upper())
        except Exception:
            pass

    def _render(self, mode: str):
        p = _PALETTE.get(mode, _PALETTE["SDR"])
        img = Image.new("RGB", (self.width, self.height), p["bg"])
        draw = ImageDraw.Draw(img)

        bar = 14
        draw.rectangle([0, 0, self.width, bar], fill=p["fg"])
        draw.rectangle([0, self.height - bar, self.width, self.height], fill=p["fg"])

        try:
            font_main = ImageFont.truetype(_FONT_BOLD, 150)
            font_sub = ImageFont.truetype(_FONT_REG, 28)
        except OSError:
            font_main = ImageFont.load_default()
            font_sub = font_main

        cx = self.width // 2
        draw.text((cx, self.height // 2 - 15), mode, font=font_main, fill=p["fg"], anchor="mm")
        sub = "HDR MODE ACTIVE" if mode == "HDR" else "SDR MODE ACTIVE"
        draw.text((cx, self.height - bar - 14), sub, font=font_sub, fill=p["sub"], anchor="mb")

        if self._bpp is None:
            self._bpp = _read_bpp(self.fb_device)

        with open(self.fb_device, "wb") as fb:
            fb.write(_to_fb_bytes(img, self._bpp))
