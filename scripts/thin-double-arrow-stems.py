#!/usr/bin/env python3
"""Thin stems on the four double-arrow resize cursors.

Edits layer8 slice-grid shapes + layer9 shadow paths (stem thinning only).
Export template paths at y~-220.5 are left unchanged to preserve symmetric arrowheads.

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

EXPORT_TEMPLATE_MASTER = (
    "m 132,-220.5 c -0.54994,0.87 -1.08461,1.77606 -1.60156,2.71289 "
    "-0.5157,0.94581 -0.98125,1.87265 -1.39844,2.78516 l 2,0.002 v 2 4 l -2,0.002 "
    "c 0.41719,0.91251 0.88274,1.83935 1.39844,2.78516 0.51695,0.93688 1.05162,1.84289 "
    "1.60156,2.71289 0.53893,-0.87 1.06705,-1.77596 1.58398,-2.71289 0.51599,-0.94635 "
    "0.9877,-1.87604 1.41602,-2.78906 l -2,0.002 v -4 -2 l 2,0.002 "
    "c -0.42832,-0.91302 -0.90003,-1.84271 -1.41602,-2.78906 "
    "C 133.06705,-218.72404 132.53893,-219.63 132,-220.5 Z"
)

# path4539 inner subpath: global head-shrink accidentally changed stem v-values here.
PATH4539_STEM_FIXES: list[tuple[str, str]] = [
    ("L 153,-242 v 2 6 l 2,-0.002", "L 153,-242 v 2 4 l 2,-0.002"),
    ("l 2,-0.002 v -6 -2 l -2,-0.002", "l 2,-0.002 v -4 -2 l -2,-0.002"),
]

# Accidental asymmetric head-shrink variants to revert.
EXPORT_TEMPLATE_VARIANTS = [
    (
        "m 132,-220.5 c -0.45,0.72 -0.90,1.47 -1.33,2.25 "
        "-0.5157,0.94581 -0.98125,1.87265 -1.39844,2.78516 l 2,0.002 v 2 6 l -2,0.002 "
        "c 0.41719,0.91251 0.88274,1.83935 1.39844,2.78516 0.51695,0.93688 1.05162,1.84289 "
        "1.60156,2.71289 0.53893,-0.87 1.06705,-1.77596 1.58398,-2.71289 0.51599,-0.94635 "
        "0.9877,-1.87604 1.41602,-2.78906 l -2,0.002 v -6 -2 l 2,0.002 "
        "c -0.42832,-0.91302 -0.90003,-1.84271 -1.41602,-2.78906 "
        "C 133.06705,-218.72404 132.53893,-219.63 132,-220.5 Z"
    ),
    (
        "m 132,-220.5 c -0.46745,0.7395 -0.92192,1.50965 -1.36133,2.30596 "
        "-0.43834,0.80394 -0.83406,1.59175 -1.18867,2.36739 l 2,0.002 v 2 6 l -2,0.002 "
        "c 0.35461,-0.42497 0.75033,0.36285 1.18867,1.16679 0.43941,0.79635 0.89388,1.56646 "
        "1.36133,2.30596 0.45809,-0.7395 0.90699,-1.50957 1.34638,-2.30596 0.43859,-0.8044 "
        "0.83954,-1.59463 1.20362,-2.3707 l -2,0.002 v -6 -2 l 2,0.002 "
        "c -0.36407,0.42333 -0.76503,-0.3669 -1.20362,-1.1713 "
        "C 132.90699,-218.99043 132.45809,-219.7605 132,-220.5 Z"
    ),
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
            if new in path_data:
                continue
            raise ValueError(f"{path_id}: expected fragment not found: {old!r}")
        path_data = path_data.replace(old, new, 1)

    if path_data == original:
        return block
    return block.replace(f'd="{original}"', f'd="{path_data}"', 1)


def patch_path4539_stem(text: str) -> str:
    for old, new in PATH4539_STEM_FIXES:
        if old in text:
            text = text.replace(old, new)
    return text


def patch_export_template(text: str) -> str:
    if EXPORT_TEMPLATE_MASTER in text and not any(v in text for v in EXPORT_TEMPLATE_VARIANTS):
        return text
    for variant in EXPORT_TEMPLATE_VARIANTS:
        if variant in text:
            text = text.replace(variant, EXPORT_TEMPLATE_MASTER)
    return text


def patch_svg(text: str) -> str:
    ids = "|".join(STEM_PATCHES.keys())
    text = re.sub(
        rf'<path\b[^>]*\bid="(?:{ids})"[^>]*/>',
        lambda m: patch_path_element(m, STEM_PATCHES),
        text,
        flags=re.DOTALL,
    )
    return patch_export_template(patch_path4539_stem(text))


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
