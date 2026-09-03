"""Render Quintom Snow slices from source-cursors.svg and build Windows cursors."""

from __future__ import annotations

import io
import struct
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from PIL import Image
import resvg_py

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Quintom_Snow Cursors" / "src" / "cursors"
SVG = SRC / "source-cursors.svg"
BITMAPS = SRC / "bitmaps"
WIN_OUT = Path.home() / "AppData" / "Local" / "Cursors" / "Quintom Snow"
SIZES = (24, 32, 48, 64, 96)
PAGE = (744, 792)
SLICE_DY = 392
INK = "{http://www.inkscape.org/namespaces/inkscape}"

WINDOWS_MAP = {
    "normal-select.cur": "left_ptr",
    "help-select.cur": "question_arrow",
    "precision-select.cur": "tcross",
    "text-select.cur": "xterm",
    "handwriting.cur": "pencil",
    "unavailable.cur": "crossed_circle",
    "vertical-resize.cur": "sb_v_double_arrow",
    "horizontal-resize.cur": "sb_h_double_arrow",
    "diagonal-resize-1.cur": "bd_double_arrow",
    "diagonal-resize-2.cur": "fd_double_arrow",
    "move.cur": "all-scroll",
    "alt-select.cur": "sb_up_arrow",
    "link-select.cur": "hand2",
}
ANIMATED = {
    "busy.ani": "watch",
    "working-in-background.ani": "left_ptr_watch",
}
ANI_SIZE = 96


def parse_slices() -> list[tuple[str, float, float, float, float]]:
    tree = ET.parse(SVG)
    slices: list[tuple[str, float, float, float, float]] = []
    for g in tree.getroot().iter("{http://www.w3.org/2000/svg}g"):
        if g.attrib.get(f"{INK}label") != "slices":
            continue
        for rect in g.findall("{http://www.w3.org/2000/svg}rect"):
            rid = rect.attrib.get("id")
            if not rid:
                continue
            x = float(rect.attrib["x"])
            y = float(rect.attrib["y"]) + SLICE_DY
            w = float(rect.attrib["width"])
            h = float(rect.attrib["height"])
            slices.append((rid, x, y, w, h))
        break
    if not slices:
        raise SystemExit("No slices found in source-cursors.svg")
    return slices


def render_sheet(size: int) -> Image.Image:
    scale = size / 24.0
    png = resvg_py.svg_to_bytes(
        svg_path=str(SVG),
        width=int(round(PAGE[0] * scale)),
        height=int(round(PAGE[1] * scale)),
    )
    return Image.open(io.BytesIO(png)).convert("RGBA")


def write_bitmaps() -> None:
    slices = parse_slices()
    print(f"slices={len(slices)}")
    for size in SIZES:
        sheet = render_sheet(size)
        scale = size / 24.0
        dest = BITMAPS / f"{size}x{size}"
        dest.mkdir(parents=True, exist_ok=True)
        for name, x, y, w, h in slices:
            box = (
                int(round(x * scale)),
                int(round(y * scale)),
                int(round((x + w) * scale)),
                int(round((y + h) * scale)),
            )
            crop = sheet.crop(box).resize((size, size), Image.Resampling.NEAREST)
            if crop.size != (size, size):
                crop = crop.resize((size, size), Image.Resampling.NEAREST)
            crop.save(dest / f"{name}.png")
        print(f"wrote {dest} ({len(slices)} png)")


def parse_in(stem: str) -> list[tuple[int, int, int, Path, int]]:
    path = BITMAPS / f"{stem}.in"
    frames: list[tuple[int, int, int, Path, int]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        size, hx, hy, rel = int(parts[0]), int(parts[1]), int(parts[2]), parts[3]
        delay = int(parts[4]) if len(parts) > 4 else 0
        frames.append((size, hx, hy, BITMAPS / rel, delay))
    return frames


def write_dib(buf: io.BytesIO, img: Image.Image) -> None:
    size = img.size[0]
    pixels = img.load()
    buf.write(struct.pack("<IiiHHIIiiII", 40, size, size * 2, 1, 32, 0, 0, 0, 0, 0, 0))
    for y in range(size - 1, -1, -1):
        for x in range(size):
            r, g, b, a = pixels[x, y]
            buf.write(struct.pack("BBBB", b, g, r, a))
    for y in range(size - 1, -1, -1):
        acc = 0
        acc_pos = 0
        wrote = 0
        for x in range(size):
            if pixels[x, y][3] <= 127:
                acc |= 1 << acc_pos
            acc_pos += 1
            if acc_pos == 8:
                buf.write(bytes([acc]))
                acc = 0
                acc_pos = 0
                wrote += 1
        if acc_pos:
            buf.write(bytes([acc]))
            wrote += 1
        while wrote % 4:
            buf.write(b"\x00")
            wrote += 1


def build_cur(frames: list[tuple[int, int, int, Image.Image]]) -> bytes:
    frames = sorted(frames, key=lambda f: f[0], reverse=True)
    header = io.BytesIO()
    header.write(struct.pack("<HHH", 0, 2, len(frames)))
    size_offset_pos = []
    for size, hx, hy, _img in frames:
        w = 0 if size >= 256 else size
        header.write(struct.pack("<BBBBHH", w, w, 0, 0, hx, hy))
        size_offset_pos.append(header.tell())
        header.write(struct.pack("<II", 0, 0))
    blobs = []
    for _size, _hx, _hy, img in frames:
        blob = io.BytesIO()
        write_dib(blob, img)
        blobs.append(blob.getvalue())
    offset = header.tell()
    for pos, blob in zip(size_offset_pos, blobs):
        header.seek(pos)
        header.write(struct.pack("<II", len(blob), offset))
        offset += len(blob)
    header.seek(0, io.SEEK_END)
    return header.getvalue() + b"".join(blobs)


def build_ani(frame_sets: list[list[tuple[int, int, int, Image.Image]]], jiffies: int) -> bytes:
    nframes = len(frame_sets)
    buf = io.BytesIO()
    buf.write(b"RIFF")
    riff_len_pos = buf.tell()
    buf.write(struct.pack("<I", 0))
    riff_start = buf.tell()
    buf.write(b"ACON")
    buf.write(b"anih")
    buf.write(struct.pack("<IIIIIIIII", 36, 36, nframes, nframes, 0, 0, 0, 0, jiffies))
    buf.write(struct.pack("<I", 0x01))
    buf.write(b"LIST")
    list_len_pos = buf.tell()
    buf.write(struct.pack("<I", 0))
    list_start = buf.tell()
    buf.write(b"fram")
    for frames in frame_sets:
        cur = build_cur(frames)
        buf.write(b"icon")
        buf.write(struct.pack("<I", len(cur)))
        buf.write(cur)
        if buf.tell() % 2:
            buf.write(b"\x00")
    end = buf.tell()
    buf.seek(riff_len_pos)
    buf.write(struct.pack("<I", end - riff_start))
    buf.seek(list_len_pos)
    buf.write(struct.pack("<I", end - list_start))
    return buf.getvalue()


def load_png(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def write_windows() -> None:
    WIN_OUT.mkdir(parents=True, exist_ok=True)
    for outfile, stem in WINDOWS_MAP.items():
        frames = []
        by_size = {}
        for size, hx, hy, png, _delay in parse_in(stem):
            if size not in by_size:
                by_size[size] = (size, hx, hy, load_png(png))
        path = WIN_OUT / outfile
        path.write_bytes(build_cur(list(by_size.values())))
        print(f"wrote {outfile}")
    for outfile, stem in ANIMATED.items():
        grouped: dict[int, list[tuple[int, int, int, Path, int]]] = defaultdict(list)
        rows = parse_in(stem)
        for row in rows:
            grouped[row[0]].append(row)
        chosen = grouped.get(ANI_SIZE) or grouped[max(grouped)]
        delay_ms = chosen[0][4] or 16
        jiffies = max(1, int(round(delay_ms * 60 / 1000)))
        frame_sets = [[(f[0], f[1], f[2], load_png(f[3]))] for f in chosen]
        path = WIN_OUT / outfile
        path.write_bytes(build_ani(frame_sets, jiffies))
        print(f"wrote {outfile} frames={len(frame_sets)}")


def main() -> int:
    write_bitmaps()
    write_windows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
