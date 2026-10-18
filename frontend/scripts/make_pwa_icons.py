"""用現有柴犬插圖產生主畫面圖示。

重跑：uv run --no-project --with pillow python scripts/make_pwa_icons.py
"""

from math import hypot
from pathlib import Path

from PIL import Image, ImageDraw

PUBLIC = Path(__file__).resolve().parents[1] / "public"
# src/index.css 的淺色主題背景與 primary，從 OKLCH 換算為 sRGB。
BACKGROUND = "#faf7ec"
PRIMARY = "#924413"
SIZE = 512


def make_icon(mascot: Image.Image, *, maskable: bool = False) -> Image.Image:
    canvas = Image.new("RGBA", (SIZE, SIZE), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), radius=100, fill=PRIMARY)

    if maskable:
        # 可遮罩圖示的安全區是半徑 40% 的圓；留到 38%，連耳朵與尾巴都保留。
        alpha = mascot.getchannel("A")
        center_x, center_y = mascot.width / 2, mascot.height / 2
        furthest_pixel = max(
            hypot(x + 0.5 - center_x, y + 0.5 - center_y)
            for y in range(mascot.height)
            for x in range(mascot.width)
            if alpha.getpixel((x, y))
        )
        scale = SIZE * 0.38 / furthest_pixel
    else:
        scale = SIZE * 0.86 / max(mascot.size)

    resized = mascot.resize(
        (round(mascot.width * scale), round(mascot.height * scale)),
        Image.Resampling.LANCZOS,
    )
    canvas.alpha_composite(
        resized, ((SIZE - resized.width) // 2, (SIZE - resized.height) // 2)
    )
    # 底色不透明，讓 iOS 與可遮罩圖示的四角也有底色。
    return canvas.convert("RGB")


def main() -> None:
    with Image.open(PUBLIC / "assets/mascot/shiba/base.webp") as source:
        mascot = source.convert("RGBA")
        mascot = mascot.crop(mascot.getbbox())

    icon = make_icon(mascot)
    for name, size in (
        ("pwa-192.png", 192),
        ("pwa-512.png", 512),
        ("apple-touch-icon-180.png", 180),
        ("favicon-32.png", 32),
    ):
        icon.resize((size, size), Image.Resampling.LANCZOS).save(
            PUBLIC / name, optimize=True
        )
        print(f"已產生 {name}（{size} × {size}）")

    make_icon(mascot, maskable=True).save(
        PUBLIC / "pwa-maskable-512.png", optimize=True
    )
    print("已產生 pwa-maskable-512.png（512 × 512）")


if __name__ == "__main__":
    main()
