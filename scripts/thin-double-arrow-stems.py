#!/usr/bin/env python3
"""Thin stems and shrink arrowheads on the four double-arrow resize cursors.

Edits:
- layer8 slice-grid shapes + layer9 shadow paths (stem thinning only; Inkscape grid)
- layer8/layer9 export template paths at y~-220.5 (smaller arrowheads, same bbox)

Does NOT touch path4507/g3506 compound templates or single-direction sb_* arrows.
"""

import re
from pathlib import Path

# Stem thinning: master -> thin stem (slice-grid + path316x shadows)
STEM_PATCHES: dict[str, list[tuple[str, str]]] = {
    "rect4955": [(" v 1 12 3 h 3 13 v -4 H 31 ", " v 1 12 3 h 2 13 v -4 H 30 ")],
    "rect4945": [(" v 12 2 h 2 12 v -2 H 30 ", " v 12 2 h 1 12 v -2 H 29 ")],
    "path3171": [(" v 1 12 3 h 3 13 v -4 H 31 ", " v 1 12 3 h 2 13 v -4 H 30 ")],
    "rect4989": [(" v 12 H 77 v 2 h 12 2 ", " v 12 H 77 v 1 h 12 2 ")],
    "rect4995": [(" v 12 H 77 v 2 h 12 2 ", " v 12 H 77 v 1 h 12 2 ")],
    "path3169": [(" H 76 v 4 h 13 3 ", " H 76 v 3 h 13 3 ")],
    "rect5021": [(" v 2 12 h 2 v -12 ", " v 2 12 h 1 v -12 ")],
    "rect5027": [(" v 2 12 h 2 v -12 ", " v 2 12 h 1 v -12 ")],
    "path3167": [(" v 1 2 13 h 4 v -12 ", " v 1 2 13 h 3 v -12 ")],
    "rect5053": [(" v 12 h 2 v -12 ", " v 12 h 1 v -12 ")],
    "rect5059": [(" v 12 h 2 v -12 ", " v 12 h 1 v -12 ")],
    "path3165": [(" h 12 v 12 h 4 v -13 ", " h 12 v 12 h 3 v -13 ")],
}

# Smaller arrowheads on exported bezier templates (same tip-to-tip bbox)
HEAD_SUBSTRINGS: list[tuple[str, str]] = [
    (
        "c -0.54994,0.87 -1.08461,1.77606 -1.60156,2.71289",
        "c -0.45,0.72 -0.90,1.47 -1.33,2.25",
    ),
    ("v 2 4", "v 2 6"),
    ("v -4 -2", "v -6 -2"),
]


def patch_path_element(match: re.Match[str], patches: dict[str, list[tuple[str, str]]]) -> str:
    block = match.group(0)
    id_match = re.search(r'\bid="([^"]+)"', block)
    if not id_match:
        return block
    path_id = id_match.group(1)
    replacements = patches.get(path_id)
    if not replacements:
        return block

    d_match = re.search(r'\bd="([^"]+)"', block)
    if not d_match:
        return block

    path_data = d_match.group(1)
    original = path_data
    for old, new in replacements:
        if old not in path_data:
            raise ValueError(f"{path_id}: expected fragment not found: {old!r}")
        path_data = path_data.replace(old, new, 1)

    if path_data == original:
        return block
    return block.replace(f'd="{original}"', f'd="{path_data}"', 1)


def patch_svg(text: str) -> str:
    ids = "|".join(STEM_PATCHES.keys())
    text = re.sub(
        rf'<path\b[^>]*\bid="(?:{ids})"[^>]*/>',
        lambda m: patch_path_element(m, STEM_PATCHES),
        text,
        flags=re.DOTALL,
    )
    for old, new in HEAD_SUBSTRINGS:
        if old not in text:
            raise ValueError(f"export template fragment not found: {old!r}")
        text = text.replace(old, new)
    return text


def main() -> None:
    targets = [
        Path("Quintom_Ink Cursors/src/cursors/source-cursors.svg"),
        Path("Quintom_Snow Cursors/src/cursors/source-cursors.svg"),
    ]
    root = Path(__file__).resolve().parents[1]
    for rel in targets:
        path = root / rel
        path.write_text(patch_svg(path.read_text()))
        print(f"patched {rel}")


if __name__ == "__main__":
    main()
