from __future__ import annotations

from dataclasses import dataclass
from html import escape
from importlib import resources
from pathlib import Path

import markdown
from weasyprint import HTML


@dataclass(slots=True)
class ConvertOptions:
    input_path: Path
    output_path: Path | None = None
    css_path: Path | None = None
    watermark_text: str | None = None


def convert_markdown_to_pdf(options: ConvertOptions) -> Path:
    input_path = options.input_path.expanduser().resolve()
    if not input_path.exists() or not input_path.is_file():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    output_path = (
        options.output_path.expanduser().resolve()
        if options.output_path
        else input_path.with_suffix(".pdf")
    )

    markdown_text = input_path.read_text(encoding="utf-8")
    pdf_bytes = render_markdown_to_pdf_bytes(
        markdown_text=markdown_text,
        title=input_path.name,
        css_path=options.css_path,
        base_path=input_path.parent,
        watermark_text=options.watermark_text,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(pdf_bytes)
    return output_path


def render_markdown_to_pdf_bytes(
    markdown_text: str,
    *,
    title: str,
    css_path: Path | None = None,
    base_path: Path | None = None,
    watermark_text: str | None = None,
) -> bytes:
    html_body = markdown.markdown(
        markdown_text,
        extensions=["fenced_code", "tables", "sane_lists", "toc"],
        output_format="html",
    )

    css_text = _read_css(css_path)
    html_document = _wrap_html_document(
        title=title,
        html_body=html_body,
        css_text=css_text,
        watermark_text=watermark_text,
    )
    resolved_base = base_path.expanduser().resolve() if base_path else Path.cwd()
    pdf_bytes = HTML(string=html_document, base_url=str(resolved_base)).write_pdf()
    if pdf_bytes is None:
        raise RuntimeError("PDF 生成失败")
    return pdf_bytes


def _read_css(css_path: Path | None) -> str:
    if css_path is not None:
        resolved_css = css_path.expanduser().resolve()
        if not resolved_css.exists() or not resolved_css.is_file():
            raise FileNotFoundError(f"CSS 文件不存在: {resolved_css}")
        return resolved_css.read_text(encoding="utf-8")

    default_css = resources.files("md2pdf").joinpath("default.css")
    return default_css.read_text(encoding="utf-8")


def _wrap_html_document(
    title: str,
    html_body: str,
    css_text: str,
    watermark_text: str | None = None,
) -> str:
    safe_title = escape(title)
    watermark_overlay, watermark_style = _build_watermark_assets(watermark_text)

    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{safe_title}</title>
    <style>
{css_text}
{watermark_style}
    </style>
  </head>
  <body>
{watermark_overlay}
    <main class="markdown-body">
{html_body}
    </main>
  </body>
</html>
"""


def _build_watermark_assets(watermark_text: str | None) -> tuple[str, str]:
    if not watermark_text:
        return "", ""

    safe_watermark = escape(watermark_text)
    line_a_items = "".join(
        [
            f'        <span class="pdf-watermark-item">{safe_watermark}</span>'
            for _ in range(8)
        ]
    )
    line_b_items = "".join(
        [
            f'        <span class="pdf-watermark-item">{safe_watermark}</span>'
            for _ in range(8)
        ]
    )
    watermark_overlay = "\n".join(
        [
            '    <div class="pdf-watermark-layer">',
            '      <div class="pdf-watermark-line pdf-watermark-line-a">',
            line_a_items,
            "      </div>",
            '      <div class="pdf-watermark-line pdf-watermark-line-b">',
            line_b_items,
            "      </div>",
            "    </div>",
        ]
    )
    watermark_style = """
.pdf-watermark-layer {
  position: fixed;
  top: -30%;
  left: -40%;
  width: 180%;
  height: 160%;
  overflow: hidden;
  pointer-events: none;
  z-index: 9999;
  transform: rotate(-29deg);
  transform-origin: center;
}

.pdf-watermark-line {
  position: absolute;
  left: -10%;
  width: 140%;
  white-space: nowrap;
}

.pdf-watermark-line-a {
  top: 32%;
}

.pdf-watermark-line-b {
  top: 62%;
}

.pdf-watermark-item {
  display: inline-block;
  font-size: 42px;
  font-weight: 700;
  letter-spacing: 4px;
  color: rgba(70, 70, 70, 0.22);
  margin-right: 140px;
  user-select: none;
  white-space: nowrap;
}
"""
    return watermark_overlay, watermark_style
