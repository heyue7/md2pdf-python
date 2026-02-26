from __future__ import annotations

import argparse
import sys
from pathlib import Path

from md2pdf.converter import ConvertOptions, convert_markdown_to_pdf


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="md2pdf",
        description="将 Markdown 文件转换为 PDF（基于 markdown + weasyprint）",
    )
    parser.add_argument("input", help="输入 Markdown 文件路径")
    parser.add_argument(
        "-o", "--output", help="输出 PDF 文件路径（默认与输入同名 .pdf）"
    )
    parser.add_argument("--css", help="自定义 CSS 文件路径")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    options = ConvertOptions(
        input_path=Path(args.input),
        output_path=Path(args.output) if args.output else None,
        css_path=Path(args.css) if args.css else None,
    )

    try:
        output_path = convert_markdown_to_pdf(options)
        print(f"PDF generated: {output_path}")
        return 0
    except Exception as exc:
        print(f"转换失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
