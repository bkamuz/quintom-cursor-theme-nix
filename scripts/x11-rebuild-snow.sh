#!/bin/sh
set -e
cd "/mnt/c/Users/kamuz/Downloads/quintom-cursor-theme-nix/Quintom_Snow Cursors/src/cursors/bitmaps"
DEST="/mnt/c/Users/kamuz/Downloads/quintom-cursor-theme-nix/Quintom_Snow Cursors/Quintom_Snow/cursors"
mkdir -p "$DEST"
grep '^xcursorgen ' ../x11-make.sh | tr -d '\r' | while read -r _cmd infile rest; do
  name="${infile%.in}"
  echo "generating $name"
  xcursorgen "$infile" "$DEST/$name"
done
ls -l "$DEST/left_ptr" "$DEST/bd_double_arrow" "$DEST/fd_double_arrow"
