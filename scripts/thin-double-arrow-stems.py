#!/usr/bin/env python3
"""Thin stems and shrink arrowheads on double-arrow resize export paths.

Edits the real Inkscape export templates (m 132,-220.5) used by
fd_double_arrow, bd_double_arrow, sb_v_double_arrow, sb_h_double_arrow.

- Stem width 2 -> 1 (insets l 2.5 / walls at 132±0.5)
- Arrowheads scaled 0.85 toward each tip (all bezier wings)
- Stem lengthened so tip-to-tip extent stays the same

Does NOT touch slice-grid angle-row shapes or single-direction sb_* arrows.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WRONG_SLICE_IDS = (
    "rect4955",
    "rect4945",
    "path3171",
    "rect4989",
    "rect4995",
    "path3169",
    "rect5021",
    "rect5027",
    "path3167",
    "rect5053",
    "rect5059",
    "path3165",
)

EXPORT_TEMPLATE_IDS = (
    "path3520",
    "path3522",
    "path3514",
    "path3516",
    "path3508",
    "path3510",
    "path1446",
    "path2614",
)

SHADOW_IDS = (
    "path4405",
    "path4455",
    "path4407",
    "path4477",
    "path4507",
    "path4527",
    "path4537",
    "path4539",
)

# Master (unpatched) export template.
EXPORT_TEMPLATE_MASTER = (
    "m 132,-220.5 c -0.54994,0.87 -1.08461,1.77606 -1.60156,2.71289 "
    "-0.5157,0.94581 -0.98125,1.87265 -1.39844,2.78516 l 2,0.002 v 2 4 l -2,0.002 "
    "c 0.41719,0.91251 0.88274,1.83935 1.39844,2.78516 0.51695,0.93688 1.05162,1.84289 "
    "1.60156,2.71289 0.53893,-0.87 1.06705,-1.77596 1.58398,-2.71289 0.51599,-0.94635 "
    "0.9877,-1.87604 1.41602,-2.78906 l -2,0.002 v -4 -2 l 2,0.002 "
    "c -0.42832,-0.91302 -0.90003,-1.84271 -1.41602,-2.78906 "
    "C 133.06705,-218.72404 132.53893,-219.63 132,-220.5 Z"
)

# Thin stem only (prior step).
EXPORT_TEMPLATE_THIN_STEM = (
    "m 132,-220.5 c -0.54994,0.87 -1.08461,1.77606 -1.60156,2.71289 "
    "-0.5157,0.94581 -0.98125,1.87265 -1.39844,2.78516 l 2.5,0.002 v 2 4 l -2.5,0.002 "
    "c 0.41719,0.91251 0.88274,1.83935 1.39844,2.78516 0.51695,0.93688 1.05162,1.84289 "
    "1.60156,2.71289 0.53893,-0.87 1.06705,-1.77596 1.58398,-2.71289 0.51599,-0.94635 "
    "0.9877,-1.87604 1.41602,-2.78906 l -2.5,0.002 v -4 -2 l 2.5,0.002 "
    "c -0.42832,-0.91302 -0.90003,-1.84271 -1.41602,-2.78906 "
    "C 133.06705,-218.72404 132.53893,-219.63 132,-220.5 Z"
)

# Thin stem + heads scaled 0.85 toward tips (mirror-symmetric), stem lengthened.
EXPORT_TEMPLATE_FINAL = (
    "m 132,-220.5 c -0.46745,0.7395 -0.92192,1.50965 -1.36133,2.30596 "
    "-0.43834,0.80394 -0.83406,1.59175 -1.18867,2.36739 l 2.05,0 v 2 5.65341 "
    "l -2.05,0 c 0.35461,0.77563 0.75033,1.56345 1.18867,2.36739 "
    "0.43941,0.79635 0.89388,1.56646 1.36133,2.30596 c 0.46745,-0.7395 "
    "0.92192,-1.50961 1.36133,-2.30596 0.43834,-0.80394 0.83406,-1.59175 "
    "1.18867,-2.36739 l -2.05,0 v -5.65341 -2 l 2.05,0 "
    "c -0.35461,-0.77563 -0.75033,-1.56345 -1.18867,-2.36739 "
    "-0.43941,-0.79631 -0.89388,-1.56646 -1.36133,-2.30596 Z"
)

STEM_EXTRA = 1.65341  # 7.65341 - 6

# Stem thinning on shadows (width), applied from master-ish fragments.
SHADOW_STEM_WIDTH: list[tuple[str, str]] = [
    ("2.27734,0.002 v 1.5 3.5 l -2.27734,0.002", "2.77734,0.002 v 1.5 3.5 l -2.77734,0.002"),
    ("2.27735,0.002 v 1.5 3.5 l -2.27735,0.002", "2.77735,0.002 v 1.5 3.5 l -2.77735,0.002"),
    ("-2.28711,0.002 v -3.5 -1.5 l 2.28711,0.004", "-2.78711,0.002 v -3.5 -1.5 l 2.78711,0.004"),
    ("2.55664,0.004 v 1 3.00195 l -2.55664,0.002", "3.05664,0.004 v 1 3.00195 l -3.05664,0.002"),
    ("-2.57422,0.002 v -2.99805 -0.99805 l 2.57422,0.002", "-3.07422,0.002 v -2.99805 -0.99805 l 3.07422,0.002"),
    ("L 130,-214 v 1 3.00195 l -2.55664,0.002", "L 130.5,-214 v 1 3.00195 l -3.05664,0.002"),
    ("L 150,-241 v 1 3.00195 l -2.55664,0.002", "L 150.5,-241 v 1 3.00195 l -3.05664,0.002"),
    ("L 150,-241 v 1 3 l -2.55469,0.002", "L 150.5,-241 v 1 3 l -3.05469,0.002"),
    ("-2.57422,0.002 V -213 v -0.99805 l 2.57422,0.002", "-3.07422,0.002 V -213 v -0.99805 l 3.07422,0.002"),
    ("-2.57422,0.002 V -240 v -0.99805 l 2.57422,0.002", "-3.07422,0.002 V -240 v -0.99805 l 3.07422,0.002"),
    ("L 132.5,-214.5 v 2.5 4.5 l 1.68555", "L 132.25,-214.5 v 2.5 4.5 l 1.93555"),
    ("L 131.5,-207.5 v -4.5 -2.5 l -1.68945", "L 131.75,-207.5 v -4.5 -2.5 l -1.93945"),
    ("l -1.68359,-0.002 v 2.5 4.5 l 1.68555,-0.002", "l -2.18359,-0.002 v 2.5 4.5 l 2.18555,-0.002"),
    ("l 1.68945,-0.002 v -4.5 -2.5 l -1.68945,-0.002", "l 2.18945,-0.002 v -4.5 -2.5 l -2.18945,-0.002"),
    ("L 153,-242 v 2 4 l 2,-0.002", "L 152.5,-242 v 2 4 l 2.5,-0.002"),
    ("l 2,-0.002 v -4 -2 l -2,-0.002", "l 2.5,-0.002 v -4 -2 l -2.5,-0.002"),
]

# After width-thinning, lengthen stem segments to preserve tip-to-tip with smaller heads.
SHADOW_STEM_LENGTH: list[tuple[str, str]] = [
    (
        f"2.77734,0.002 v 1.5 3.5 l -2.77734,0.002",
        f"2.77734,0.002 v 1.5 {3.5 + STEM_EXTRA:.5f} l -2.77734,0.002",
    ),
    (
        f"2.77735,0.002 v 1.5 3.5 l -2.77735,0.002",
        f"2.77735,0.002 v 1.5 {3.5 + STEM_EXTRA:.5f} l -2.77735,0.002",
    ),
    (
        f"-2.78711,0.002 v -3.5 -1.5 l 2.78711,0.004",
        f"-2.78711,0.002 v {-3.5 - STEM_EXTRA:.5f} -1.5 l 2.78711,0.004",
    ),
    (
        f"3.05664,0.004 v 1 3.00195 l -3.05664,0.002",
        f"3.05664,0.004 v 1 {3.00195 + STEM_EXTRA:.5f} l -3.05664,0.002",
    ),
    (
        f"-3.07422,0.002 v -2.99805 -0.99805 l 3.07422,0.002",
        f"-3.07422,0.002 v {-2.99805 - STEM_EXTRA:.5f} -0.99805 l 3.07422,0.002",
    ),
    (
        f"L 130.5,-214 v 1 3.00195 l -3.05664,0.002",
        f"L 130.5,-214 v 1 {3.00195 + STEM_EXTRA:.5f} l -3.05664,0.002",
    ),
    (
        f"L 150.5,-241 v 1 3.00195 l -3.05664,0.002",
        f"L 150.5,-241 v 1 {3.00195 + STEM_EXTRA:.5f} l -3.05664,0.002",
    ),
    (
        f"L 150.5,-241 v 1 3 l -3.05469,0.002",
        f"L 150.5,-241 v 1 {3 + STEM_EXTRA:.5f} l -3.05469,0.002",
    ),
    (
        f"L 132.25,-214.5 v 2.5 4.5 l 1.93555",
        f"L 132.25,-214.5 v 2.5 {4.5 + STEM_EXTRA:.5f} l 1.93555",
    ),
    (
        f"L 131.75,-207.5 v -4.5 -2.5 l -1.93945",
        f"L 131.75,-207.5 v {-4.5 - STEM_EXTRA:.5f} -2.5 l -1.93945",
    ),
    (
        f"l -2.18359,-0.002 v 2.5 4.5 l 2.18555,-0.002",
        f"l -2.18359,-0.002 v 2.5 {4.5 + STEM_EXTRA:.5f} l 2.18555,-0.002",
    ),
    (
        f"l 2.18945,-0.002 v -4.5 -2.5 l -2.18945,-0.002",
        f"l 2.18945,-0.002 v {-4.5 - STEM_EXTRA:.5f} -2.5 l -2.18945,-0.002",
    ),
    (
        f"L 152.5,-242 v 2 4 l 2.5,-0.002",
        f"L 152.5,-242 v 2 {4 + STEM_EXTRA:.5f} l 2.5,-0.002",
    ),
    (
        f"l 2.5,-0.002 v -4 -2 l -2.5,-0.002",
        f"l 2.5,-0.002 v {-4 - STEM_EXTRA:.5f} -2 l -2.5,-0.002",
    ),
]


def extract_path_block(text: str, path_id: str) -> tuple[str, str] | None:
    id_attr = f'id="{path_id}"'
    idx = text.find(id_attr)
    if idx < 0:
        return None
    start = text.rfind("<path", 0, idx)
    if start < 0:
        return None
    end = text.find("/>", idx)
    if end < 0:
        return None
    block = text[start : end + 2]
    d_match = re.search(r'\bd="([^"]*)"', block)
    if not d_match:
        return None
    return block, d_match.group(1)


def replace_path_d(text: str, path_id: str, new_d: str) -> str:
    found = extract_path_block(text, path_id)
    if not found:
        raise ValueError(f"path id not found: {path_id}")
    block, old_d = found
    if old_d == new_d:
        return text
    new_block = block.replace(f'd="{old_d}"', f'd="{new_d}"', 1)
    return text.replace(block, new_block, 1)


def restore_ids_from_master(text: str, master_text: str, ids: tuple[str, ...]) -> str:
    for path_id in ids:
        master = extract_path_block(master_text, path_id)
        current = extract_path_block(text, path_id)
        if not master or not current:
            raise ValueError(f"missing {path_id}")
        _, master_d = master
        _, current_d = current
        if current_d != master_d:
            text = replace_path_d(text, path_id, master_d)
            print(f"  restored {path_id} from master")
    return text


def patch_export_templates(text: str) -> str:
    known = {EXPORT_TEMPLATE_MASTER, EXPORT_TEMPLATE_THIN_STEM, EXPORT_TEMPLATE_FINAL}
    # Prior asymmetric head-shrink attempt (replaced by mirror-symmetric FINAL).
    known.add(
        "m 132,-220.5 c -0.46745,0.7395 -0.92192,1.50965 -1.36133,2.30596 "
        "-0.43834,0.80394 -0.83406,1.59175 -1.18867,2.36739 l 2.05,0.002 v 2 5.64941 "
        "l -2.05,0.002 c 0.35461,0.77563 0.75033,1.56345 1.18867,2.36739 "
        "0.43941,0.79635 0.89388,1.56646 1.36133,2.30596 0.45809,-0.7395 "
        "0.90699,-1.50957 1.34638,-2.30596 0.43859,-0.8044 0.83954,-1.59463 "
        "1.20362,-2.3707 l -2.05,0.002 v -5.64941 -2 l 2.05,0.002 "
        "c -0.36407,-0.77905 -0.76503,-1.56929 -1.20362,-2.37369 "
        "C 132.90699,-218.99043 132.45809,-219.7605 132,-220.5 Z"
    )
    for path_id in EXPORT_TEMPLATE_IDS:
        found = extract_path_block(text, path_id)
        if not found:
            raise ValueError(f"missing export template {path_id}")
        _, d = found
        if d == EXPORT_TEMPLATE_FINAL:
            continue
        if d in known:
            text = replace_path_d(text, path_id, EXPORT_TEMPLATE_FINAL)
            print(f"  export {path_id} -> thin stem + small heads")
        else:
            raise ValueError(f"{path_id}: unexpected template path data")
    return text


def apply_shadow_replacements(d: str, replacements: list[tuple[str, str]]) -> str:
    for old, new in replacements:
        if old in d:
            d = d.replace(old, new)
    return d


def patch_shadows(text: str, master_text: str) -> str:
    """Restore shadows from master, then apply stem width-thin only.

    Head shapes in soft shadows stay at master size (blurred halo). Stem
    length is NOT extended here — lengthening without head shrink made
    shadows longer than the cursor tip-to-tip.
    """
    for path_id in SHADOW_IDS:
        master = extract_path_block(master_text, path_id)
        if not master:
            raise ValueError(f"master missing shadow {path_id}")
        _, master_d = master
        d = apply_shadow_replacements(master_d, SHADOW_STEM_WIDTH)
        text = replace_path_d(text, path_id, d)
        print(f"  shadow {path_id} patched from master")
    return text


def patch_svg(text: str, master_text: str) -> str:
    text = restore_ids_from_master(text, master_text, WRONG_SLICE_IDS)
    text = patch_export_templates(text)
    text = patch_shadows(text, master_text)
    return text


def load_master_svg(rel: Path) -> str:
    return subprocess.check_output(
        ["git", "show", f"master:{rel.as_posix()}"],
        cwd=ROOT,
        text=True,
    )


def main() -> None:
    targets = [
        Path("Quintom_Ink Cursors/src/cursors/source-cursors.svg"),
        Path("Quintom_Snow Cursors/src/cursors/source-cursors.svg"),
    ]
    for rel in targets:
        path = ROOT / rel
        print(f"patching {rel}")
        master_text = load_master_svg(rel)
        path.write_text(patch_svg(path.read_text(), master_text))
        print(f"wrote {rel}")


if __name__ == "__main__":
    main()
