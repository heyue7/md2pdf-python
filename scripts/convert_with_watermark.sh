#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <input_md> [watermark_text] [output_pdf]" >&2
  exit 1
fi

INPUT_MD="$1"
WATERMARK_TEXT="${2:-CONFIDENTIAL}"
OUTPUT_PDF="${3:-}"

if [[ ! -f "$INPUT_MD" ]]; then
  echo "Input markdown file not found: $INPUT_MD" >&2
  exit 1
fi

if [[ -z "$OUTPUT_PDF" ]]; then
  input_dir="$(dirname "$INPUT_MD")"
  input_base="$(basename "$INPUT_MD")"
  input_stem="${input_base%.*}"
  OUTPUT_PDF="$input_dir/${input_stem}_wm.pdf"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
  "$PROJECT_ROOT/.venv/bin/python" -m md2pdf.cli "$INPUT_MD" -o "$OUTPUT_PDF" --watermark-text "$WATERMARK_TEXT"
else
  md2pdf "$INPUT_MD" -o "$OUTPUT_PDF" --watermark-text "$WATERMARK_TEXT"
fi

echo "Watermarked PDF generated: $OUTPUT_PDF"
