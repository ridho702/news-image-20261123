#!/usr/bin/env python3
"""World news, Monday 23 November 2026, in one image.

Draws a 1024x1024 newspaper-style infographic with the Python standard
library only (zlib + struct for the PNG encoder, everything else is plain
pixel math), and writes it to $MAKEFUN_OUTPUT_DIR/entry.png (or /output).

No network, no randomness, no clock: two runs produce identical bytes.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 231)
INK = (26, 35, 50)
NAVY = (20, 33, 61)
WHITE = (255, 255, 255)
RED = (180, 35, 24)
BLUE = (29, 78, 137)
GOLD = (192, 138, 30)
GREEN = (46, 125, 50)
GREY = (216, 210, 196)
TEAL = (11, 127, 166)
PANEL_BLUE = (232, 238, 245)
ORANGE = (214, 106, 24)
YELLOW = (232, 196, 66)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, '#' on, '.' off. Uppercase + digits +
# the punctuation this image uses. Written from scratch for this entry.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
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
    "X": ("10001", "01010", "00100", "00100", "00100", "01010", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "00110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10001", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00010", "00100", "00100", "00100"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "01100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "%": ("10001", "10010", "00010", "00100", "01000", "01001", "10001"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "10000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "$": ("00100", "01111", "10100", "01100", "00101", "11110", "00100"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "\u2022": ("00000", "00000", "01110", "01110", "01110", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
}

# ---------------------------------------------------------------- canvas


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def hline(self, x, y, w, c):
        self.fill_rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.fill_rect(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def thick_line(self, x0, y0, x1, y1, t, c):
        for k in range(-t // 2, t // 2 + 1):
            self.line(x0, y0 + k, x1, y1 + k, c)
            self.line(x0 + k, y0, x1 + k, y1, c)

    def circle(self, cx, cy, r, c, fill=False):
        for yy in range(-r, r + 1):
            half = int((r * r - yy * yy) ** 0.5)
            if fill:
                self.fill_rect(cx - half, cy + yy, 2 * half + 1, 1, c)
            else:
                self.set(cx - half, cy + yy, c)
                self.set(cx + half, cy + yy, c)

    def ellipse(self, cx, cy, rx, ry, c, fill=False):
        for yy in range(-ry, ry + 1):
            t = 1.0 - (yy * yy) / float(ry * ry)
            half = int(rx * (t ** 0.5)) if t > 0 else 0
            if fill:
                self.fill_rect(cx - half, cy + yy, 2 * half + 1, 1, c)
            else:
                self.set(cx - half, cy + yy, c)
                self.set(cx + half, cy + yy, c)

    def poly(self, pts, c):
        # Filled polygon, scanline fill.
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(len(pts)):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % len(pts)]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[k]), y, int(xs[k + 1]) - int(xs[k]) + 1, 1, c)

    # -- text -------------------------------------------------------------
    def text(self, x, y, s, scale, c):
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[" "])
            for r in range(7):
                row = g[r]
                for col in range(5):
                    if row[col] == "1":
                        self.fill_rect(cx + col * scale, y + r * scale,
                                       scale, scale, c)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def text_center(self, y, s, scale, c, x0=0, x1=None):
        x1 = self.w if x1 is None else x1
        x = x0 + (x1 - x0 - self.text_w(s, scale)) // 2
        self.text(x, y, s, scale, c)

    def wrap(self, s, scale, width):
        """Greedy word wrap; returns list of lines."""
        words = s.split(" ")
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if self.text_w(trial, scale) <= width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines


# ---------------------------------------------------------------- icons

def draw_globe(cv, cx, cy, r, c):
    cv.circle(cx, cy, r, c)
    cv.ellipse(cx, cy, r // 2, r, c)
    cv.ellipse(cx, cy, r, r // 2, c)
    cv.hline(cx - r, cy, 2 * r + 1, c)


def draw_building(cv, x, y, w, h, c, win):
    cv.fill_rect(x, y, w, h, c)
    for wy in range(y + 10, y + h - 8, 16):
        for wx in range(x + 8, x + w - 8, 16):
            cv.fill_rect(wx, wy, 8, 8, win)
    # crack
    cv.thick_line(x + w // 2, y + 4, x + w // 2 - 8, y + h // 2, 2, RED)
    cv.thick_line(x + w // 2 - 8, y + h // 2, x + w // 2 + 6, y + h - 4, 2, RED)


def draw_ship(cv, cx, cy, s, c):
    # hull, slightly listing
    cv.poly([(cx - 52 * s, cy), (cx + 52 * s, cy - 8 * s),
             (cx + 40 * s, cy + 16 * s), (cx - 40 * s, cy + 16 * s)], c)
    cv.fill_rect(cx - 30 * s, cy - 22 * s, 60 * s, 20 * s, c)
    cv.vline(cx + 18 * s, cy - 40 * s, 20 * s, c)
    cv.poly([(cx + 18 * s, cy - 40 * s), (cx + 38 * s, cy - 30 * s),
             (cx + 18 * s, cy - 30 * s)], RED)
    for k, wy in enumerate((cy + 26 * s, cy + 34 * s, cy + 42 * s)):
        for x in range(cx - 60 * s, cx + 61 * s, 12 * s):
            off = (x // (12 * s) + k) % 2
            cv.fill_rect(x, wy + off * 2 * s, 8 * s, 2 * s, BLUE)


def draw_chart(cv, x, y, w, h, c):
    cv.vline(x, y, h, INK)
    cv.hline(x, y + h - 1, w, INK)
    pts = [(x + 8, y + 14), (x + 30, y + 30), (x + 52, y + 26),
           (x + 74, y + 52), (x + 96, y + 66), (x + 116, y + 88)]
    for a, b in zip(pts, pts[1:]):
        cv.thick_line(a[0], a[1], b[0], b[1], 3, c)
    # arrowhead
    cv.poly([(x + 116, y + 88), (x + 100, y + 84), (x + 112, y + 70)], c)


def draw_capitol(cv, cx, y, w, c):
    cv.ellipse(cx, y + 26, w // 2, 26, c, fill=True)
    cv.fill_rect(cx - w // 2, y + 26, w, 10, c)
    for k in range(-2, 3):
        cv.fill_rect(cx + k * (w // 6) - 3, y + 40, 6, 34, c)
    cv.fill_rect(cx - w // 2 - 6, y + 74, w + 12, 8, c)
    cv.vline(cx, y - 16, 16, c)
    cv.poly([(cx, y - 16), (cx + 16, y - 11), (cx, y - 6)], RED)


def draw_tanker(cv, cx, cy, s, c):
    cv.fill_rect(cx - 70 * s, cy, 140 * s, 18 * s, c)
    cv.poly([(cx + 70 * s, cy), (cx + 86 * s, cy + 9 * s),
             (cx + 70 * s, cy + 18 * s)], c)
    for k in range(4):
        cv.fill_rect(cx - 62 * s + k * 32 * s, cy - 16 * s, 26 * s, 16 * s,
                     (BLUE if k % 2 == 0 else GOLD))
    # flame
    cv.poly([(cx - 30 * s, cy - 16 * s), (cx - 18 * s, cy - 44 * s),
             (cx - 6 * s, cy - 16 * s)], ORANGE)
    cv.poly([(cx - 24 * s, cy - 16 * s), (cx - 18 * s, cy - 32 * s),
             (cx - 12 * s, cy - 16 * s)], YELLOW)
    for k, wy in enumerate((cy + 26 * s, cy + 34 * s)):
        for x in range(cx - 80 * s, cx + 81 * s, 12 * s):
            off = (x // (12 * s) + k) % 2
            cv.fill_rect(x, wy + off * 2 * s, 8 * s, 2 * s, BLUE)


# ---------------------------------------------------------------- layout

def panel(cv, x, y, w, h, accent):
    cv.fill_rect(x, y, w, h, WHITE)
    cv.fill_rect(x, y, w, 6, accent)
    cv.hline(x, y + h - 1, w, GREY)
    cv.vline(x, y, h, GREY)
    cv.vline(x + w - 1, y, h, GREY)
    cv.hline(x, y, w, GREY)


def story_panel(cv, x, y, w, h, accent, kicker, headline, summary, icon):
    panel(cv, x, y, w, h, accent)
    tx = x + 18
    tw = w - 36 - 118  # text width, icon on the right
    cv.text(tx, y + 16, kicker, 2, accent)
    lines = cv.wrap(headline, 3, tw)
    yy = y + 42
    for ln in lines[:2]:
        cv.text(tx, yy, ln, 3, INK)
        yy += 25
    slines = cv.wrap(summary, 2, tw)
    yy += 4
    for ln in slines[:3]:
        cv.text(tx, yy, ln, 2, (74, 84, 100))
        yy += 17
    icon(x + w - 108, y + 44)


def build():
    cv = Canvas(W, H, PAPER)

    # ---- masthead
    cv.fill_rect(0, 0, W, 150, NAVY)
    cv.text_center(26, "WORLD NEWS", 9, PAPER)
    cv.fill_rect(212, 108, 600, 3, GOLD)
    cv.text_center(122, "MONDAY, 23 NOVEMBER 2026", 4, GOLD)

    # ---- lead story: COP31
    lx, ly, lw, lh = 28, 166, 968, 262
    panel(cv, lx, ly, lw, lh, RED)
    draw_globe(cv, lx + 120, ly + 130, 74, BLUE)
    cv.circle(lx + 168, ly + 178, 22, RED, fill=True)
    cv.thick_line(lx + 158, ly + 168, lx + 178, ly + 188, 4, WHITE)
    cv.thick_line(lx + 178, ly + 168, lx + 158, ly + 188, 4, WHITE)
    tx = lx + 250
    cv.text(tx, ly + 22, "CLIMATE - ANTALYA, TURKEY", 2, RED)
    for i, ln in enumerate(cv.wrap("COP31 ENDS WITH NO DEAL", 5, 660)):
        cv.text(tx, ly + 52 + i * 42, ln, 5, INK)
    yy = ly + 150
    for ln in cv.wrap(
            "TALKS IN ANTALYA COLLAPSE AFTER THE EU AND 130 NATIONS "
            "REJECT A DRAFT WITH NO FOSSIL-FUEL PHASE-OUT.", 3, 660):
        cv.text(tx, yy, ln, 3, (74, 84, 100))
        yy += 26

    # ---- grid of four
    gx, gy = 28, 444
    pw, ph, gap = 476, 168, 16
    story_panel(cv, gx, gy, pw, ph, RED,
                "WAR IN UKRAINE - DYMER",
                "RUSSIAN STRIKE KILLS AT LEAST 10",
                "A BOY, 7, IS PULLED ALIVE FROM A HIT APARTMENT BLOCK "
                "NORTH OF KYIV.",
                lambda ix, iy: draw_building(cv, ix, iy, 84, 96, INK, PAPER))
    story_panel(cv, gx + pw + gap, gy, pw, ph, NAVY,
                "LIBYA - BENGHAZI",
                "RUSSIAN WARSHIP SINKS IN LIBYA PORT",
                "THE MERKURY GOES DOWN AT ITS BERTH IN A SUSPECTED "
                "DRONE ATTACK.",
                lambda ix, iy: draw_ship(cv, ix + 46, iy + 40, 1, NAVY))
    story_panel(cv, gx, gy + ph + gap, pw, ph, RED,
                "MARKETS - TOKYO",
                "AI SELL-OFF SINKS NIKKEI 5.1%",
                "ASIAN SHARES SINK ON U.S. TECH ROUT; HONG KONG AT "
                "19-MONTH LOW.",
                lambda ix, iy: draw_chart(cv, ix - 6, iy + 6, 122, 96, RED))
    story_panel(cv, gx + pw + gap, gy + ph + gap, pw, ph, BLUE,
                "U.S. POLITICS",
                "DEMOCRATS WIN RECORD MAJORITY",
                "LARGEST SINCE 1992: AT LEAST 258 SEATS AFTER A NORTH "
                "CAROLINA RECOUNT.",
                lambda ix, iy: draw_capitol(cv, ix + 46, iy + 10, 92, BLUE))

    # ---- bottom story: Hormuz
    bx, by, bw, bh = 28, 812, 968, 134
    cv.fill_rect(bx, by, bw, bh, PANEL_BLUE)
    cv.fill_rect(bx, by, bw, 6, TEAL)
    cv.hline(bx, by + bh - 1, bw, GREY)
    cv.vline(bx, by, bh, GREY)
    cv.vline(bx + bw - 1, by, bh, GREY)
    cv.hline(bx, by, bw, GREY)
    draw_tanker(cv, bx + 130, by + 62, 1, INK)
    tx = bx + 250
    cv.text(tx, by + 16, "MIDDLE EAST - STRAIT OF HORMUZ", 2, TEAL)
    for i, ln in enumerate(cv.wrap(
            "TANKERS ABLAZE NEAR HORMUZ AS U.S.-IRAN TENSIONS SPIKE",
            4, 690)):
        cv.text(tx, by + 40 + i * 32, ln, 4, INK)
    yy = by + 104
    for ln in cv.wrap("TWO SUPERTANKERS CATCH FIRE AFTER REPORTED MINE "
                      "HITS; TRUMP THREATENS TO SINK IRANIAN VESSELS.",
                      2, 690):
        cv.text(tx, yy, ln, 2, (74, 84, 100))
        yy += 17

    # ---- footer
    cv.text_center(972, "SIX STORIES FROM ONE DAY  \u2022  23 NOVEMBER 2026",
                   2, (90, 96, 110))
    return cv


# ---------------------------------------------------------------- PNG


def png_bytes(cv):
    raw = b"".join(
        b"\x00" + bytes(cv.px[y * cv.w * 3:(y + 1) * cv.w * 3])
        for y in range(cv.h))
    def chunk(tag, data):
        body = tag + data
        return (struct.pack(">I", len(data)) + body +
                struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(build())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
