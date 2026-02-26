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
    html_body = markdown.markdown(
        markdown_text,
        extensions=["fenced_code", "tables", "sane_lists", "toc"],
        output_format="html5",
    )

    css_text = _read_css(options.css_path)
    html_document = _wrap_html_document(
        title=input_path.name,
        html_body=html_body,
        css_text=css_text,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_document, base_url=str(input_path.parent)).write_pdf(
        str(output_path)
    )
    return output_path


def _read_css(css_path: Path | None) -> str:
    if css_path is not None:
        resolved_css = css_path.expanduser().resolve()
        if not resolved_css.exists() or not resolved_css.is_file():
            raise FileNotFoundError(f"CSS 文件不存在: {resolved_css}")
        return resolved_css.read_text(encoding="utf-8")

    default_css = resources.files("md2pdf").joinpath("default.css")
    return default_css.read_text(encoding="utf-8")


def _wrap_html_document(title: str, html_body: str, css_text: str) -> str:
    safe_title = escape(title)
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{safe_title}</title>
    <style>
{css_text}
    </style>
  </head>
  <body>
    <main class="markdown-body">
{html_body}
    </main>
  </body>
</html>
"""
