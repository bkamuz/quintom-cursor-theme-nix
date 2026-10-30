#!/usr/bin/env python3
"""Regenerate README preview_ink.png / preview_snow.png from 96x96 bitmaps."""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

LAYOUT: list[list[str]] = [
    [
        "left_ptr",
        "right_ptr",
        "context-menu",
        "link",
        "circle",
        "copy",
        "pointer-move",
        "left_ptr_watch",
        "watch",
    ],
    [
        "hand1",
        "grabbing",
        "hand2",
        "dnd-none",
        "dnd-ask",
        "dnd-copy",
        "dnd-link",
        "dnd-move",
        "dnd-no-drop",
    ],
    [
        "top_side",
        "bottom_side",
        "right_side",
        "left_side",
        "bottom_left_corner",
        "bottom_right_corner",
        "top_left_corner",
        "top_right_corner",
    ],
    [
        "fd_double_arrow",
        "bd_double_arrow",
        "sb_v_double_arrow",
        "sb_h_double_arrow",
        "sb_right_arrow",
        "sb_left_arrow",
        "sb_up_arrow",
        "sb_down_arrow",
    ],
    [
        "question_arrow",
        "pencil",
        "xterm",
        "vertical-text",
        "zoom-in",
        "zoom-out",
        "crossed_circle",
        "X_cursor",
    ],
    [
        "ll_angle",
        "lr_angle",
        "ul_angle",
        "ur_angle",
        "top_tee",
        "bottom_tee",
        "left_tee",
        "right_tee",
    ],
    ["cross", "crosshair", "tcross", "dotbox", "plus", "move", "all-scroll"],
]

# Content centers measured from the historical preview collage.
XS = [58, 253, 446, 638, 830, 1022, 1214, 1404, 1590]
YS = [64, 257, 447, 638, 830, 1023, 1214]
WIDTH, HEIGHT = 1643, 1280
CURSOR_SIZE = 96

ANIM_FRAME = {
    "left_ptr_watch": "left_ptr_watch_0001",
    "watch": "watch_0001",
}


def resolve_bitmap(bitmaps_dir: Path, name: str) -> Path:
    candidates = [
        bitmaps_dir / f"{ANIM_FRAME.get(name, name)}.png",
        bitmaps_dir / f"{name}.png",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"bitmap not found for {name} in {bitmaps_dir}")


def make_preview(bitmaps_dir: Path, out_path: Path) -> None:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
    for row_index, row in enumerate(LAYOUT):
        for col_index, name in enumerate(row):
            image = Image.open(resolve_bitmap(bitmaps_dir, name)).convert("RGBA")
            if image.size != (CURSOR_SIZE, CURSOR_SIZE):
                image = image.resize((CURSOR_SIZE, CURSOR_SIZE), Image.Resampling.LANCZOS)
            x = int(round(XS[col_index] - CURSOR_SIZE / 2))
            y = int(round(YS[row_index] - CURSOR_SIZE / 2))
            canvas.alpha_composite(image, (x, y))
    canvas.save(out_path)
    print(f"wrote {out_path.relative_to(ROOT)}")


def main() -> None:
    make_preview(
        ROOT / "Quintom_Ink Cursors/src/cursors/bitmaps/96x96",
        ROOT / "preview_ink.png",
    )
    make_preview(
        ROOT / "Quintom_Snow Cursors/src/cursors/bitmaps/96x96",
        ROOT / "preview_snow.png",
    )


if __name__ == "__main__":
    main()
