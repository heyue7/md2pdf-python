from __future__ import annotations

import logging
import re
import ssl
import urllib.request
from dataclasses import dataclass
from html import escape
from importlib import resources
from pathlib import Path

import markdown
from weasyprint import HTML
from weasyprint import default_url_fetcher

logger = logging.getLogger(__name__)


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

    source_text = input_path.read_text(encoding="utf-8")
    if input_path.suffix.lower() in {".html", ".htm"}:
        pdf_bytes = render_html_to_pdf_bytes(
            html_text=source_text,
            title=input_path.name,
            css_path=options.css_path,
            base_path=input_path.parent,
            watermark_text=options.watermark_text,
        )
    else:
        pdf_bytes = render_markdown_to_pdf_bytes(
            markdown_text=source_text,
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
    if _should_render_markdown_as_html(markdown_text):
        return render_html_to_pdf_bytes(
            html_text=markdown_text,
            title=title,
            css_path=css_path,
            base_path=base_path,
            watermark_text=watermark_text,
        )

    html_body = markdown.markdown(
        markdown_text,
        extensions=["fenced_code", "tables", "sane_lists", "toc"],
        output_format="html",
    )

    return render_html_to_pdf_bytes(
        html_text=html_body,
        title=title,
        css_path=css_path,
        base_path=base_path,
        watermark_text=watermark_text,
        body_only=True,
    )


def render_html_to_pdf_bytes(
    html_text: str,
    *,
    title: str,
    css_path: Path | None = None,
    base_path: Path | None = None,
    watermark_text: str | None = None,
    body_only: bool = False,
) -> bytes:
    css_text = _read_css(css_path)
    html_document = (
        _wrap_html_document(
            title=title,
            html_body=html_text,
            css_text=css_text,
            watermark_text=watermark_text,
        )
        if body_only
        else _compose_html_document(
            title=title,
            html_text=html_text,
            css_text=css_text,
            watermark_text=watermark_text,
        )
    )

    html_document = _fix_inline_flex_for_weasyprint(html_document)

    resolved_base = base_path.expanduser().resolve() if base_path else Path.cwd()
    pdf_bytes = HTML(
        string=html_document,
        base_url=str(resolved_base),
        url_fetcher=_url_fetcher,
    ).write_pdf()
    if pdf_bytes is None:
        raise RuntimeError("PDF 生成失败")
    return pdf_bytes


_HTML_BLOCK_TAG_RE = re.compile(
    r"<\s*(style|div|section|article|main|header|footer|aside|table|figure|figcaption|img|p|h1|h2|h3|h4|h5|h6|ul|ol|li|blockquote|pre|svg)\b",
    re.IGNORECASE,
)
_INLINE_FLEX_RE = re.compile(
    r'(?P<prefix>style="[^"]*?)display\s*:\s*flex\b',
    re.IGNORECASE,
)
_IMG_HEIGHT_FULL_RE = re.compile(
    r'(?P<prefix><img\b[^>]*?style="[^"]*?)height\s*:\s*100%\b',
    re.IGNORECASE,
)


def _should_render_markdown_as_html(markdown_text: str) -> bool:
    stripped_text = markdown_text.lstrip()
    if not stripped_text.startswith("<"):
        return False

    if _looks_like_full_html_document(stripped_text):
        return True

    return len(_HTML_BLOCK_TAG_RE.findall(stripped_text)) >= 2


def _fix_inline_flex_for_weasyprint(html_text: str) -> str:
    html_text = _INLINE_FLEX_RE.sub(r"\g<prefix>display:block", html_text)
    return _IMG_HEIGHT_FULL_RE.sub(r"\g<prefix>height:auto", html_text)


_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def _make_permissive_ssl_context() -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _url_fetcher(
    url: str, timeout: int = 10, ssl_context: ssl.SSLContext | None = None
) -> dict:
    """Fetch remote http(s) resources with browser-like headers so that
    CDN / object-storage servers (e.g. Aliyun OSS) don't reject the request."""
    if url.startswith(("http://", "https://")):
        logger.info("获取远程资源: %s", url)
        request = urllib.request.Request(
            url, headers={"User-Agent": _BROWSER_USER_AGENT}
        )
        contexts = [
            ssl_context or ssl.create_default_context(),
            _make_permissive_ssl_context(),
        ]
        last_error: Exception | None = None
        for ctx in contexts:
            try:
                response = urllib.request.urlopen(request, timeout=timeout, context=ctx)
                data = response.read()
                content_type = response.headers.get("Content-Type", "")
                mime = content_type.split(";")[0].strip()
                logger.info("远程资源获取成功: %s (%d bytes, %s)", url, len(data), mime)
                return {"string": data, "mime_type": mime}
            except ssl.SSLError as exc:
                last_error = exc
                logger.warning("SSL 校验失败，尝试跳过校验: %s - %s", url, exc)
                continue
            except Exception as exc:
                last_error = exc
                break
        logger.error("远程资源获取失败: %s - %s", url, last_error, exc_info=True)
        return {"string": b"", "mime_type": "application/octet-stream"}

    return default_url_fetcher(url, timeout=timeout, ssl_context=ssl_context)


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


def _compose_html_document(
    title: str,
    html_text: str,
    css_text: str,
    watermark_text: str | None = None,
) -> str:
    if _looks_like_full_html_document(html_text):
        return _augment_existing_html_document(
            html_text=html_text,
            css_text=css_text,
            watermark_text=watermark_text,
        )

    safe_title = escape(title)
    watermark_overlay, watermark_style = _build_watermark_assets(watermark_text)
    overlay_markup = f"{watermark_overlay}\n" if watermark_overlay else ""

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
{overlay_markup}{html_text}
  </body>
</html>
"""


def _looks_like_full_html_document(html_text: str) -> bool:
    lowered_html = html_text.lower()
    return "<html" in lowered_html or "<body" in lowered_html or "<head" in lowered_html


def _augment_existing_html_document(
    html_text: str,
    css_text: str,
    watermark_text: str | None = None,
) -> str:
    watermark_overlay, watermark_style = _build_watermark_assets(watermark_text)
    style_block = f"<style>\n{css_text}\n{watermark_style}\n</style>"

    if "</head>" in html_text:
        html_text = html_text.replace("</head>", f"{style_block}\n</head>", 1)
    else:
        html_text = f"{style_block}\n{html_text}"

    if watermark_overlay:
        lowered_html = html_text.lower()
        body_open_index = lowered_html.find("<body")
        if body_open_index != -1:
            body_open_end = html_text.find(">", body_open_index)
            if body_open_end != -1:
                html_text = (
                    f"{html_text[: body_open_end + 1]}\n{watermark_overlay}"
                    f"{html_text[body_open_end + 1 :]}"
                )
            else:
                html_text = f"{watermark_overlay}\n{html_text}"
        else:
            html_text = f"{watermark_overlay}\n{html_text}"

    return html_text


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
