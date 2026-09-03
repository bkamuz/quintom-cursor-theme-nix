#!/usr/bin/env python3
"""Thin stems on the four double-arrow resize cursor export paths.

Edits the real Inkscape export templates (m 132,-220.5) used by
fd_double_arrow, bd_double_arrow, sb_v_double_arrow, sb_h_double_arrow.

Does NOT touch:
- slice-grid angle-row shapes (ll/lr/ul/ur_angle)
- single-direction sb_* arrows
- arrowhead bezier coefficients (keeps heads symmetric)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Paths that were wrongly thinned on the angle-row slice grid; restore from master.
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

# Fill + white-outline clones of the vertical double-arrow template.
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

# Soft-shadow companions for the same four cursors.
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

# Stem insets only: width 2 -> 1, heads unchanged.
EXPORT_STEM_REPLACEMENTS: list[tuple[str, str]] = [
    ("l 2,0.002 v 2 4 l -2,0.002", "l 2.5,0.002 v 2 4 l -2.5,0.002"),
    ("l -2,0.002 v -4 -2 l 2,0.002", "l -2.5,0.002 v -4 -2 l 2.5,0.002"),
]

# Soft-shadow outer stem jumps grow by 0.5 when walls move inward (width 2 -> 1).
SHADOW_SOFT_OUTER: list[tuple[str, str]] = [
    ("2.27734,0.002 v 1.5 3.5 l -2.27734,0.002", "2.77734,0.002 v 1.5 3.5 l -2.77734,0.002"),
    ("2.27735,0.002 v 1.5 3.5 l -2.27735,0.002", "2.77735,0.002 v 1.5 3.5 l -2.77735,0.002"),
    ("-2.28711,0.002 v -3.5 -1.5 l 2.28711,0.004", "-2.78711,0.002 v -3.5 -1.5 l 2.78711,0.004"),
]

# Harder outline-shadow stem jumps (path4455 / path4477).
SHADOW_HARD_REL: list[tuple[str, str]] = [
    ("2.55664,0.004 v 1 3.00195 l -2.55664,0.002", "3.05664,0.004 v 1 3.00195 l -3.05664,0.002"),
    ("-2.57422,0.002 v -2.99805 -0.99805 l 2.57422,0.002", "-3.07422,0.002 v -2.99805 -0.99805 l 3.07422,0.002"),
]

# Absolute stem walls on path4527 / path4537 / path4539 outer.
SHADOW_HARD_ABS: list[tuple[str, str]] = [
    ("L 130,-214 v 1 3.00195 l -2.55664,0.002", "L 130.5,-214 v 1 3.00195 l -3.05664,0.002"),
    ("L 150,-241 v 1 3.00195 l -2.55664,0.002", "L 150.5,-241 v 1 3.00195 l -3.05664,0.002"),
    ("L 150,-241 v 1 3 l -2.55469,0.002", "L 150.5,-241 v 1 3 l -3.05469,0.002"),
    ("-2.57422,0.002 V -213 v -0.99805 l 2.57422,0.002", "-3.07422,0.002 V -213 v -0.99805 l 3.07422,0.002"),
    ("-2.57422,0.002 V -240 v -0.99805 l 2.57422,0.002", "-3.07422,0.002 V -240 v -0.99805 l 3.07422,0.002"),
]

# path4507 absolute inner hole: keep ~0.5 inset from thinned fill walls.
SHADOW_SOFT_INNER_ABS: list[tuple[str, str]] = [
    ("L 132.5,-214.5 v 2.5 4.5 l 1.68555", "L 132.25,-214.5 v 2.5 4.5 l 1.93555"),
    ("L 131.5,-207.5 v -4.5 -2.5 l -1.68945", "L 131.75,-207.5 v -4.5 -2.5 l -1.93945"),
]

# path4405 / path4407 relative inner hole jumps.
SHADOW_SOFT_INNER_REL: list[tuple[str, str]] = [
    ("l -1.68359,-0.002 v 2.5 4.5 l 1.68555,-0.002", "l -2.18359,-0.002 v 2.5 4.5 l 2.18555,-0.002"),
    ("l 1.68945,-0.002 v -4.5 -2.5 l -1.68945,-0.002", "l 2.18945,-0.002 v -4.5 -2.5 l -2.18945,-0.002"),
]

# path4539 compound hole uses the rotated template stem (width 2 -> 1).
PATH4539_HOLE: list[tuple[str, str]] = [
    ("L 153,-242 v 2 4 l 2,-0.002", "L 152.5,-242 v 2 4 l 2.5,-0.002"),
    ("l 2,-0.002 v -4 -2 l -2,-0.002", "l 2.5,-0.002 v -4 -2 l -2.5,-0.002"),
]

ALL_SHADOW_REPLACEMENTS: list[tuple[str, str]] = (
    SHADOW_SOFT_OUTER
    + SHADOW_HARD_REL
    + SHADOW_HARD_ABS
    + SHADOW_SOFT_INNER_ABS
    + SHADOW_SOFT_INNER_REL
    + PATH4539_HOLE
)


def extract_path_block(text: str, path_id: str) -> tuple[str, str] | None:
    """Return (full path element, d attribute) for id, or None."""
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


def apply_replacements(path_data: str, replacements: list[tuple[str, str]], path_id: str) -> str:
    for old, new in replacements:
        if old not in path_data:
            if new in path_data:
                continue
            raise ValueError(f"{path_id}: expected fragment not found: {old!r}")
        path_data = path_data.replace(old, new)
    return path_data


def restore_ids_from_master(text: str, master_text: str, ids: tuple[str, ...]) -> str:
    for path_id in ids:
        master = extract_path_block(master_text, path_id)
        current = extract_path_block(text, path_id)
        if not master:
            raise ValueError(f"master missing {path_id}")
        if not current:
            raise ValueError(f"current missing {path_id}")
        _, master_d = master
        _, current_d = current
        if current_d != master_d:
            text = replace_path_d(text, path_id, master_d)
            print(f"  restored {path_id} from master")
    return text


def thin_export_templates(text: str) -> str:
    for path_id in EXPORT_TEMPLATE_IDS:
        found = extract_path_block(text, path_id)
        if not found:
            raise ValueError(f"missing export template {path_id}")
        _, d = found
        new_d = apply_replacements(d, EXPORT_STEM_REPLACEMENTS, path_id)
        text = replace_path_d(text, path_id, new_d)
        if new_d != d:
            print(f"  thinned export {path_id}")
    return text


def thin_shadows(text: str) -> str:
    for path_id in SHADOW_IDS:
        found = extract_path_block(text, path_id)
        if not found:
            raise ValueError(f"missing shadow {path_id}")
        _, d = found
        original = d
        for old, new in ALL_SHADOW_REPLACEMENTS:
            if old in d:
                d = d.replace(old, new)
        if d != original:
            text = replace_path_d(text, path_id, d)
            print(f"  thinned shadow {path_id}")
        else:
            print(f"  shadow unchanged {path_id}")
    return text


def patch_svg(text: str, master_text: str) -> str:
    text = restore_ids_from_master(text, master_text, WRONG_SLICE_IDS)
    text = thin_export_templates(text)
    text = thin_shadows(text)
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
