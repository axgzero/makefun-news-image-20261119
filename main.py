#!/usr/bin/env python3
"""Render one 1024x1024 PNG summing up the world news of Thursday
19 November 2026. Pure standard library: a tiny raster canvas, a
5x7 bitmap font, and a hand-rolled PNG encoder (zlib + struct).
Writes to $MAKEFUN_OUTPUT_DIR/entry.png, or /output/entry.png.
Deterministic: the same input always produces the same bytes.
"""
import os
import struct
import zlib

W, H = 1024, 1024

# ---- palette ---------------------------------------------------------
PAPER = (247, 243, 232)
INK = (18, 24, 34)
NAVY = (15, 42, 74)
NAVY2 = (23, 68, 112)
GOLD = (201, 162, 39)
RED = (178, 34, 34)
TEAL = (14, 110, 105)
WHITE = (255, 255, 255)
GREY = (90, 96, 104)
LIGHT = (233, 228, 214)
SKY = (135, 190, 220)
GREEN = (34, 120, 60)

# ---- 5x7 bitmap font (uppercase; lowercase maps to uppercase) -------
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def wrap(text, max_width, scale):
    """Greedy word wrap; returns list of lines that fit max_width."""
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(max(0, y), min(self.h, y + h)):
            base = (yy * self.w + max(0, x)) * 3
            n = min(self.w, x + w) - max(0, x)
            if n > 0:
                self.px[base:base + n * 3] = bytes(color) * n

    def hline(self, x, y, w, color, t=1):
        self.rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.rect(x, y, t, h, color)

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= r else 0
            self.rect(cx - dx, yy, dx * 2 + 1, 1, color)

    def ring(self, cx, cy, r, color, t=3):
        for k in range(t):
            rr = r - k
            for yy in range(cy - rr, cy + rr + 1):
                d = (rr * rr - (yy - cy) ** 2)
                if d < 0:
                    continue
                dx = int(d ** 0.5)
                self.set(cx - dx, yy, color)
                self.set(cx + dx, yy, color)

    def triangle(self, x0, y0, x1, y1, x2, y2, color):
        # scanline fill of a triangle
        pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        def interp(y, p, q):
            if q[1] == p[1]:
                return p[0]
            return p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1])
        for y in range(ay, cy + 1):
            if y < by:
                xa, xb = interp(y, (ax, ay), (bx, by)), interp(y, (ax, ay), (cx, cy))
            else:
                xa, xb = interp(y, (bx, by), (cx, cy)), interp(y, (ax, ay), (cx, cy))
            self.rect(int(min(xa, xb)), y, int(abs(xb - xa)) + 1, 1, color)

    def text(self, x, y, s, scale, color):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_center(self, cx, y, s, scale, color):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color)

    def para(self, x, y, s, scale, color, max_width, leading=None):
        lh = leading if leading is not None else 9 * scale
        for line in wrap(s, max_width, scale):
            self.text(x, y, line, scale, color)
            y += lh
        return y


def png_bytes(canvas):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


# ---- little drawn icons ------------------------------------------------
def draw_globe(c, cx, cy, r):
    c.circle(cx, cy, r, SKY)
    c.ring(cx, cy, r, NAVY, 4)
    c.circle(cx - r // 3, cy - r // 4, r // 4, GREEN)
    c.circle(cx + r // 3, cy + r // 5, r // 5, GREEN)
    c.rect(cx - r, cy - 2, r * 2, 3, NAVY2)
    c.rect(cx - 2, cy - r, 3, r * 2, NAVY2)


def draw_flag_stripes(c, x, y, w, h):
    # three stacked flag bars: USA / China / Russia
    bh = h // 3
    c.rect(x, y, w, bh, (178, 34, 52))          # USA red band
    c.rect(x, y, w // 3, bh, NAVY)             # USA blue canton
    c.rect(x, y + bh, w, bh, (222, 41, 16))    # China red
    c.text(x + w // 2 - 6, y + bh + 3, "*", 2, GOLD)
    c.rect(x, y + 2 * bh, w, bh // 3 + 2, WHITE)
    c.rect(x, y + 2 * bh + bh // 3, w, bh // 3 + 2, (0, 57, 166))
    c.rect(x, y + 2 * bh + 2 * bh // 3, w, bh // 3 + 2, (213, 0, 50))


def draw_scales(c, x, y, s):
    # balance scales: pillar, beam, two pans
    c.rect(x + s // 2 - 3, y, 6, s, GOLD)
    c.rect(x, y, s + 6, 5, GOLD)
    c.rect(x + s // 2 - 12, y - 8, 30, 6, GOLD)
    for px in (x - 6, x + s - 6):
        c.vline(px + 8, y - 6, 22, GOLD, 2)
        c.triangle(px, y + 18, px + 20, y + 18, px + 10, y + 34, GOLD)


def draw_bars(c, x, y, w, h, color):
    heights = [int(h * f) for f in (0.35, 0.55, 0.45, 0.8, 1.0)]
    bw = w // 6
    for i, bh in enumerate(heights):
        c.rect(x + i * (bw + 4), y + h - bh, bw, bh, color)


def draw_tanker(c, x, y, w, h):
    c.rect(x, y + h // 2, w, h // 3, (40, 60, 80))       # hull
    c.rect(x + w // 6, y, w // 3, h // 2, (200, 60, 40))  # funnel
    c.triangle(x + w // 2, y - 18, x + w // 2 + 14, y + 4,
               x + w // 2 - 14, y + 4, (240, 140, 30))    # flame
    c.triangle(x + w // 2 + 16, y - 8, x + w // 2 + 26, y + 4,
               x + w // 2 + 6, y + 4, GOLD)
    for i in range(5):                                     # waves
        c.rect(x + i * (w // 5), y + h - 6, w // 7, 4, SKY)


def draw_flame_building(c, x, y, w, h):
    c.rect(x, y + h // 3, w, 2 * h // 3, (120, 80, 60))   # building
    for row in range(3):
        for col in range(4):
            c.rect(x + 8 + col * (w // 4), y + h // 3 + 10 + row * 18,
                   10, 10, GOLD)
    c.triangle(x + w // 2 - 14, y, x + w // 2 + 14, y + h // 3,
               x + w // 2 - 14, y + h // 3, (240, 120, 20))
    c.triangle(x + w // 2 + 4, y + 10, x + w // 2 + 22, y + h // 3,
               x + w // 2 + 4, y + h // 3, GOLD)


def draw_leaf(c, x, y, s):
    c.circle(x + s // 2, y + s // 2, s // 2, GREEN)
    c.rect(x + s // 2 - 2, y + 6, 4, s - 6, (20, 80, 40))
    c.rect(x + 8, y + s // 2, s - 16, 4, (20, 80, 40))


def panel(c, x, y, w, h, kicker, kcolor):
    c.rect(x, y, w, h, WHITE)
    c.rect(x, y, w, 4, kcolor)
    c.rect(x, y, 4, h, kcolor)
    c.text(x + 16, y + 16, kicker, 2, kcolor)


def headline(c, x, y, s, scale, max_width, color=INK):
    yy = y
    for line in wrap(s, max_width, scale):
        c.text(x, yy, line, scale, color)
        yy += 9 * scale
    return yy


# ---- the front page ----------------------------------------------------
def render():
    c = Canvas(W, H, PAPER)

    # masthead
    c.rect(0, 0, W, 118, NAVY)
    c.rect(0, 118, W, 5, GOLD)
    c.text_center(W // 2, 18, "THE WORLD IN ONE PICTURE", 4, WHITE)
    c.text_center(W // 2, 62, "THURSDAY 19 NOVEMBER 2026", 3, GOLD)
    c.text(24, 92, "THE DAY'S WORLD NEWS  -  ONE PAGE", 2, (180, 200, 220))
    c.text(W - 24 - text_width("PRICE: ONE DAY OF NEWS", 2), 92,
           "PRICE: ONE DAY OF NEWS", 2, (180, 200, 220))

    # ---- lead story: Shenzhen summit ----------------------------------
    x, y, w, h = 16, 138, 992, 218
    c.rect(x, y, w, h, WHITE)
    c.rect(x, y, w, 5, RED)
    draw_globe(c, x + 105, y + 108, 62)
    draw_flag_stripes(c, x + 200, y + 62, 96, 84)
    tx = x + 322
    c.text(tx, y + 16, "1  SHENZHEN  -  THE BIG SUMMIT", 2, RED)
    yy = headline(c, tx, y + 44, "TRUMP, XI AND PUTIN MEET FACE TO FACE",
                  3, w - 340)
    c.para(tx, yy + 6,
           "First ever three-way summit in Shenzhen. The three leaders "
           "sign a four-point Declaration toward Peace: no nuclear war, "
           "UN reform, more oil supply, and a warning to the ICC. "
           "No deal on Ukraine or Iran.", 2, INK, w - 340)

    # ---- middle grid: four stories ------------------------------------
    gy, gh, gw, gap = 372, 218, 488, 16
    # A: ICJ Rohingya
    panel(c, 16, gy, gw, gh, "2  THE HAGUE  -  JUSTICE", NAVY2)
    draw_scales(c, 40, gy + 62, 84)
    yy = headline(c, 150, gy + 48, "WORLD COURT: MYANMAR COMMITTED GENOCIDE",
                  2, gw - 170)
    c.para(150, yy + 4, "The ICJ rules Myanmar's army acted with genocidal "
           "intent against the Rohingya in 2017. Gambia brought the case. "
           "The court orders restitution and investigations.", 2, INK,
           gw - 170)
    # B: Anthropic IPO
    panel(c, 16 + gw + gap, gy, gw, gh, "3  NEW YORK  -  MARKETS", TEAL)
    draw_bars(c, 16 + gw + gap + 22, gy + 118, 96, 72, TEAL)
    yy = headline(c, 16 + gw + gap + 134, gy + 48,
                  "ANTHROPIC IPO: $83 A SHARE, OPENS AT $111.50", 2, gw - 170)
    c.para(16 + gw + gap + 134, yy + 4, "The Claude maker's record debut "
           "raises $81 billion on Nasdaq. Shares jump 34% on the first "
           "trade, the biggest AI listing yet.", 2, INK, gw - 170)
    # C: Hormuz / Iran
    panel(c, 16, gy + gh + gap, gw, gh, "4  STRAIT OF HORMUZ  -  WAR AT SEA", RED)
    draw_tanker(c, 40, gy + gh + gap + 96, 96, 60)
    yy = headline(c, 150, gy + gh + gap + 48,
                  "TANKERS HIT AS US-IRAN WAR ESCALATES", 2, gw - 170)
    c.para(150, yy + 4, "Tankers catch fire after mine strikes; an ADNOC "
           "ship reports 11 crew hurt, one missing. Kuwait repels an "
           "Iranian attack. The US Senate votes 51-48 against curbing "
           "Trump's Iran war powers.", 2, INK, gw - 170)
    # D: Bangladesh
    panel(c, 16 + gw + gap, gy + gh + gap, gw, gh,
          "5  DHAKA  -  UNREST", (150, 90, 20))
    draw_flame_building(c, 16 + gw + gap + 30, gy + gh + gap + 84, 84, 96)
    yy = headline(c, 16 + gw + gap + 134, gy + gh + gap + 48,
                  "BANGLADESH BURNS AFTER HASINA VERDICT", 2, gw - 170)
    c.para(16 + gw + gap + 134, yy + 4, "Violence spreads to 28 districts "
           "after Sheikh Hasina is sentenced to death. Protesters set "
           "fire to interim leader Yunus's ancestral home.", 2, INK,
           gw - 170)

    # ---- bottom band: COP31 + also today ------------------------------
    by, bh = 840, 168
    c.rect(16, by, 992, bh, NAVY)
    c.rect(16, by, 992, 4, GOLD)
    draw_leaf(c, 40, by + 52, 56)
    c.text(116, by + 18, "6  ANTALYA  -  CLIMATE", 2, GOLD)
    yy = headline(c, 116, by + 44, "COP31: MINISTERS RACE TO UNBLOCK TALKS",
                  2, 380, WHITE)
    c.para(116, yy + 4, "Negotiators in Turkey await a final text as "
           "fossil-fuel language is cut from the draft.", 2,
           (210, 220, 235), 380)
    c.vline(520, by + 16, bh - 32, GOLD, 2)
    c.text(544, by + 18, "ALSO ON 19 NOVEMBER", 2, GOLD)
    also = [
        "DENMARK 109-0 BACKS GREENLAND PACT",
        "EU PROPOSES 45BN LOAN TO UKRAINE",
        "GTA VI LAUNCHES WORLDWIDE",
        "VAN GOGH SELLS FOR $190.4M",
    ]
    yy = by + 48
    for item in also:
        c.text(544, yy, "- " + item, 2, WHITE)
        yy += 26
    return c


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    data = png_bytes(render())
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
