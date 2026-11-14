#!/usr/bin/env python3
"""Generate Y2K-styled Plymouth assets for the pixie-y2k splash theme.

All assets are drawn as RGBA PNGs with PIL from exact color values, so the
look is deterministic (no AI guesses). Palette: Y2K chrome silver + rice cyan
#33ccff on a deep space-navy background.
"""
import glob
import math
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.expanduser("~/y2k-splash")
FONT_PATH = "/usr/share/fonts/noto/NotoSans-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/noto/NotoSans-Bold.ttf"

CYAN = (51, 204, 255)
WHITE = (255, 255, 255)
SILVER_TOP = (240, 244, 250)
SILVER_BOT = (148, 160, 178)


def rot(rect, cx, cy, ang_deg):
    """x,y rotated around (cx,cy); angle 0 = pointing right (12 o'clock at -90)."""
    a = math.radians(ang_deg - 90)
    return cx + rect * math.cos(a), cy + rect * math.sin(a)


def make_throbbers(size=96, frames=30):
    """Y2K loading ring: cyan arc with white tip, cyan outer glow, subtle ring track."""
    for i in range(frames):
        ang = i * (360 / frames)
        im = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
        # two layers: first the glow, drawn wide then blurred; then the core
        for glow, w, col in ((1, 10, (51, 204, 255, 110)), (0, 5, (*CYAN, 255))):
            d = ImageDraw.Draw(im)
            d.arc([size // 2, size // 2, size + size // 2, size + size // 2],
                  start=ang, end=ang + 300, fill=col, width=w)
            if glow:
                im = im.filter(ImageFilter.GaussianBlur(3))
        c = size  # center in the doubled canvas
        # white Y2K "comet" tip at the arc head
        tx, ty = rot(size * 0.5, c, c, ang)
        d = ImageDraw.Draw(im)
        d.ellipse([tx - 4, ty - 4, tx + 4, ty + 4], fill=(*WHITE, 255))
        # dim full track so the arc has a presence while rotating
        d.arc([size // 2, size // 2, size + size // 2, size + size // 2],
              start=0, end=360, fill=(51, 204, 255, 34), width=1)
        im = im.filter(ImageFilter.GaussianBlur(0.4))
        im = im.resize((size, size), Image.LANCZOS)
        im.save(os.path.join(HERE, f"throbber-{i+1:04d}.png"))


def make_entry(w=305, h=34):
    """Password pill: translucent dark glass + cyan border, Y2K console chic."""
    s = 4  # supersample — draw big, shrink for antialiasing
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = 14 * s
    # glass body
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=r,
                        fill=(16, 18, 28, 178))
    # cyan border + soft inner cyan edge for glow
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=r,
                        outline=(*CYAN, 235), width=2 * s)
    d.rounded_rectangle([3*s, 3*s, w*s-1-3*s, h*s-1-3*s], radius=r-s,
                        outline=(51, 204, 255, 60), width=1 * s)
    im = im.resize((w, h), Image.LANCZOS)
    im.save(os.path.join(HERE, "entry.png"))


def make_bullet(size=10):
    im = Image.new("RGBA", (size * 4, size * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([size, size, size * 3, size * 3], fill=(*CYAN, 255))
    glow = im.filter(ImageFilter.GaussianBlur(3))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(glow)
    out.alpha_composite(im)
    out = out.resize((size, size), Image.LANCZOS)
    out.save(os.path.join(HERE, "bullet.png"))


def make_watermark(w=460, h=110):
    """Chrome-gradient 'p i x i e' with cyan halo — the Y2K signature."""
    ss = 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    txt = "p i x i e"
    fnt = ImageFont.truetype(FONT_BOLD, 64 * ss)
    tw = d.textlength(txt, font=fnt)
    x0, y0 = (w * ss - tw) / 2, (h * ss - 74 * ss) / 2
    # cyan halo
    halo = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(halo).text((x0, y0), txt, font=fnt, fill=(*CYAN, 170))
    halo = halo.filter(ImageFilter.GaussianBlur(9 * ss))
    halo.save("/tmp/y2k-halo.png")
    gl = Image.open("/tmp/y2k-halo.png")  # reload for safety
    im.alpha_composite(gl)
    # chrome fill: draw text then darken fill by drawing a vertical gradient mask
    txt_layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d2 = ImageDraw.Draw(txt_layer)
    d2.text((x0, y0), txt, font=fnt, fill=(255, 255, 255, 255))
    bbox = txt_layer.getbbox()
    grad = Image.new("RGBA", im.size, (0, 0, 0, 0))
    if bbox:
        top, bot = bbox[1], bbox[3]
        for y in range(top, bot + 1):
            t = (y - top) / max(1, bot - top)
            col = tuple(int(SILVER_TOP[i] + (SILVER_BOT[i] - SILVER_TOP[i]) * t)
                        for i in range(3))
            ImageDraw.Draw(grad).line([(0, y), (im.size[0], y)], fill=(*col, 255))
    grad.putalpha(txt_layer.split()[3])
    im.alpha_composite(grad)
    # thin cyan outline around the chrome for that y2k "ice" edge
    edge = txt_layer.split()[3].point(lambda a: 255 if a > 10 else 0)
    import PIL.ImageChops as IC
    outline = IC.subtract(edge.filter(ImageFilter.MaxFilter(3)), edge)
    oim = Image.new("RGBA", im.size, (0, 0, 0, 0))
    oim.putalpha(outline)
    ImageDraw.Draw(oim).rectangle([0, 0, im.size[0], im.size[1]],
                                  fill=(*CYAN, 255))
    oim.putalpha(outline)
    im.alpha_composite(oim)
    im = im.resize((w, h), Image.LANCZOS)
    im.save(os.path.join(HERE, "watermark.png"))


def make_bg_mock():
    """Full 1366x768 mock of the splash for eyeballing, no reboot needed."""
    W, H = 1366, 768
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    top, bot = (5, 8, 16), (11, 29, 51)
    for y in range(H):
        t = y / H
        col = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        ImageDraw.Draw(im).line([(0, y), (W, y)], fill=(*col, 255))
    # y2k starfield sprinkle (deterministic: no random)
    d = ImageDraw.Draw(im)
    sky = ((6, 9, 18), (10, 26, 46))
    for y in range(H):
        t = y / H
        col = tuple(int(sky[0][i] + (sky[1][i] - sky[0][i]) * t) for i in range(3))
        d.line([(0, y), (W, y)], fill=(*col, 255))
    stars = [(109, 92, 2), (320, 130, 1), (494, 61, 2), (700, 170, 1),
             (880, 80, 2), (1042, 145, 1), (1211, 63, 2), (1330, 199, 1),
             (59, 256, 2), (255, 310, 1), (476, 410, 2), (914, 352, 1),
             (1127, 463, 2), (1284, 290, 1), (749, 530, 2), (176, 594, 1)]
    for (x, y, r) in stars:
        d.ellipse([x - r, y - r, x + r, y + r], fill=(200, 232, 255, 120))
    # watermark bottom-center
    wm = Image.open(os.path.join(HERE, "watermark.png"))
    im.alpha_composite(wm, ((W - wm.size[0]) // 2, H - wm.size[1] - 24))
    # password pill at dialog spot (.382 vertically)
    entry = Image.open(os.path.join(HERE, "entry.png"))
    ey = int(H * 0.382) - entry.size[1] // 2
    im.alpha_composite(entry, ((W - entry.size[0]) // 2, ey))
    # bullets inside pill
    b = Image.open(os.path.join(HERE, "bullet.png"))
    for k in range(8):
        im.alpha_composite(b, ((W - entry.size[0]) // 2 + 53 + k * 21,
                               ey + entry.size[1] // 2 - b.size[1] // 2))
    # spinner below pill (.7 vertically per config)
    th = Image.open(os.path.join(HERE, "throbber-0008.png"))
    im.alpha_composite(th, ((W - th.size[0]) // 2, int(H * 0.70) - th.size[1] // 2))
    im.convert("RGB").save(os.path.join(HERE, "mock-splash.png"))


if __name__ == "__main__":
    make_throbbers()
    make_entry()
    make_bullet()
    make_watermark()
    make_bg_mock()
    print("assets generated in", HERE)
    for f in sorted(glob.glob(os.path.join(HERE, "throbber-*.png")))[:2]:
        print(" ", os.path.basename(f), Image.open(f).size)
    print("  watermark.png", Image.open(os.path.join(HERE, "watermark.png")).size)
    print("  entry.png", Image.open(os.path.join(HERE, "entry.png")).size)
    print("  bullet.png", Image.open(os.path.join(HERE, "bullet.png")).size)
    print("  mock-splash.png written")
