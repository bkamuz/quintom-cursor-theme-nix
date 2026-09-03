## Creating & Modifying Icons

Edit the source in **[Inkscape](https://inkscape.org)** — that is the program this theme is built in. Do not use Figma, Illustrator, or Boxy SVG for the master file: they rewrite Inkscape layers and slice IDs.

Open the matching `source-cursors.svg`:

- Snow: `Quintom_Snow Cursors/src/cursors/source-cursors.svg`
- Ink: `Quintom_Ink Cursors/src/cursors/source-cursors.svg`

In **Layers**, turn on:

- `labels` — names of each 24×24 cell
- `slices` — the blue squares; each square’s **ID** is the cursor filename (`fd_double_arrow`, `left_ptr`, …)
- `hotspots` — the active pixel (keep this aligned if you move a shape)
- `cursors` — the actual artwork; edit only this layer

Work inside the 24×24 cell. After saving, rebuild with `render-cursors.py source-cursors.svg`, then `x11-make.sh`.

### Corner resize arrows

The two two-headed diagonals look swapped if you map X11 names onto Windows by name.

| Look | Window corner | X11 file | Windows |
| --- | --- | --- | --- |
| `\` top-left ↔ bottom-right | NW–SE | `bd_double_arrow` | SizeNWSE |
| `/` top-right ↔ bottom-left | NE–SW | `fd_double_arrow` | SizeNESW |

Linux aliases already follow that: `nwse-resize` → `bd_double_arrow`, `nesw-resize` → `fd_double_arrow`. Do not swap the SVG drawings unless you also retarget those aliases.
