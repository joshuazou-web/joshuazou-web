#!/usr/bin/env bash
# One-shot build: content.html -> <name>.html (editable), <name>.pdf, <name>.png, <name>.docx
# Usage: build.sh <workdir> <output-name> [docx_line_twips=212]
#   <workdir> holds content.html plus logos/ and icons/ (copy them from ../assets).
#   Outputs are written into <workdir>/out/.
set -euo pipefail
WORK="$(cd "$1" && pwd)"; NAME="$2"; LINE="${3:-212}"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$WORK/out"; mkdir -p "$OUT"

# ASu-skills provides the editor toolbar/frame that the template shell is inlined into.
ASU="${ASU_DIR:-}"
if [ -z "$ASU" ]; then
  ASU="$(find "$HOME/.claude/plugins" -path '*scripts/build-asu-resume.mjs' 2>/dev/null | head -1 | xargs -r dirname | xargs -r dirname)"
fi
if [ -z "$ASU" ] || [ ! -f "$ASU/scripts/build-asu-resume.mjs" ]; then
  ASU=/tmp/ASu-skills
  [ -d "$ASU" ] || git clone -q --depth 1 https://github.com/Hisn00w/ASu-skills.git "$ASU"
fi

# Node deps: playwright is global in cloud sessions; docx is installed on demand.
DEPS=/tmp/resume-polish-node
node -e "require('docx')" 2>/dev/null || { [ -d "$DEPS/node_modules/docx" ] || npm install -s --prefix "$DEPS" docx >/dev/null; }
export NODE_PATH="$(npm root -g):$DEPS/node_modules"
python3 -c "import pypdfium2" 2>/dev/null || pip install -q pypdfium2 >/dev/null

node "$ASU/scripts/build-asu-resume.mjs" "$WORK/content.html" "$OUT/$NAME.html" >/dev/null
rm -rf "$OUT/logos" "$OUT/icons"; cp -r "$WORK/logos" "$WORK/icons" "$OUT/"
node "$HERE/render.cjs" "$OUT/$NAME.html" "$OUT/$NAME.pdf"
node "$HERE/measure.cjs" "$OUT/$NAME.html"
node "$HERE/svg2png.cjs" "$OUT/logos" >/dev/null
node "$HERE/extract.cjs" "$WORK/content.html" "$OUT/resume.json" >/dev/null
node "$HERE/build-docx.cjs" "$OUT/resume.json" "$OUT/$NAME.docx" "$LINE" "$OUT"

# Optional check: how many pages the DOCX renders to (LibreOffice approximates Word).
if command -v soffice >/dev/null; then
  TMP=$(mktemp -d); cp "$OUT/$NAME.docx" "$TMP/check.docx"
  (cd "$TMP" && timeout 120 soffice --headless --convert-to pdf check.docx >/dev/null 2>&1) || true
  [ -f "$TMP/check.pdf" ] && python3 -c "import pypdfium2 as p,sys;print('docx pages (LibreOffice)',len(p.PdfDocument(sys.argv[1])))" "$TMP/check.pdf"
  rm -rf "$TMP"
fi
echo "done -> $OUT/$NAME.{html,pdf,png,docx}"
