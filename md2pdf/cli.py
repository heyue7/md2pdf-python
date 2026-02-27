from __future__ import annotations

import argparse
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from md2pdf.converter import (
    ConvertOptions,
    convert_markdown_to_pdf,
    render_markdown_to_pdf_bytes,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="md2pdf",
        description="将 Markdown 文件转换为 PDF，或启动 HTTP 转换服务",
    )
    parser.add_argument("input", nargs="?", help="输入 Markdown 文件路径")
    parser.add_argument(
        "-o", "--output", help="输出 PDF 文件路径（默认与输入同名 .pdf）"
    )
    parser.add_argument("--css", help="自定义 CSS 文件路径")
    parser.add_argument(
        "--watermark",
        action="store_true",
        help="开启水印（默认文字 CONFIDENTIAL）",
    )
    parser.add_argument("--watermark-text", help="自定义水印文字")
    parser.add_argument("--serve", action="store_true", help="启动 HTTP 服务模式")
    parser.add_argument(
        "--host", default="127.0.0.1", help="HTTP 服务监听地址（默认 127.0.0.1）"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=20706,
        help="HTTP 服务监听端口（默认 20706）",
    )
    return parser


def _handler_factory(default_css_path: Path | None) -> type[BaseHTTPRequestHandler]:
    class ConvertHandler(BaseHTTPRequestHandler):
        server_version = "md2pdf-http/0.1"

        def _send_json(self, status: HTTPStatus, payload: dict[str, str]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path != "/health":
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            self._send_json(HTTPStatus.OK, {"status": "ok"})

        def do_POST(self) -> None:
            if self.path not in {"/convert", "/convert-watermark"}:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return

            payload = self._read_json_payload()
            if payload is None:
                return

            watermark_text: str | None = None
            if self.path == "/convert-watermark":
                watermark_value = payload.get("watermark_text", "CONFIDENTIAL")
                if not isinstance(watermark_value, str) or not watermark_value.strip():
                    self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {"error": "field 'watermark_text' must be a non-empty string"},
                    )
                    return
                watermark_text = watermark_value

            self._handle_convert(payload, watermark_text)

        def _read_json_payload(self) -> dict[str, object] | None:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0:
                self._send_json(
                    HTTPStatus.BAD_REQUEST, {"error": "request body is empty"}
                )
                return None

            try:
                body = self.rfile.read(content_length)
                payload = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid json body"})
                return None

            if not isinstance(payload, dict):
                self._send_json(
                    HTTPStatus.BAD_REQUEST, {"error": "json root must be object"}
                )
                return None

            return payload

        def _handle_convert(
            self,
            payload: dict[str, object],
            watermark_text: str | None,
        ) -> None:
            markdown_text = payload.get("markdown")
            if not isinstance(markdown_text, str):
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "field 'markdown' must be a string"},
                )
                return

            css_path = _resolve_css_path(payload.get("css_path"), default_css_path)
            filename = _resolve_filename(payload.get("filename"))

            safe_filename = filename.replace('"', "").replace("\n", "")

            try:
                pdf_bytes = render_markdown_to_pdf_bytes(
                    markdown_text=markdown_text,
                    title="http-request.md",
                    css_path=css_path,
                    watermark_text=watermark_text,
                )
            except Exception as exc:
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": f"convert failed: {exc}"},
                )
                return

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Length", str(len(pdf_bytes)))
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{safe_filename}"',
            )
            self.end_headers()
            self.wfile.write(pdf_bytes)

    return ConvertHandler


def _resolve_css_path(
    css_path_value: object,
    default_css_path: Path | None,
) -> Path | None:
    if isinstance(css_path_value, str) and css_path_value.strip():
        return Path(css_path_value)
    return default_css_path


def _resolve_filename(filename_value: object) -> str:
    if isinstance(filename_value, str) and filename_value.strip():
        return filename_value
    return "output.pdf"


def run_server(host: str, port: int, css_path: Path | None) -> int:
    server = ThreadingHTTPServer((host, port), _handler_factory(css_path))
    print(f"HTTP server started: http://{host}:{port}")
    print("POST /convert with JSON: {'markdown': '...'}")
    print(
        "POST /convert-watermark with JSON: {'markdown': '...', 'watermark_text': 'CONFIDENTIAL'}"
    )
    print("GET /health for health check")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nHTTP server stopped")
    finally:
        server.server_close()
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.serve:
        try:
            return run_server(
                host=args.host,
                port=args.port,
                css_path=Path(args.css) if args.css else None,
            )
        except Exception as exc:
            print(f"启动服务失败: {exc}", file=sys.stderr)
            return 1

    if not args.input:
        print("缺少输入文件：非服务模式下必须提供 input 参数", file=sys.stderr)
        return 2

    options = ConvertOptions(
        input_path=Path(args.input),
        output_path=Path(args.output) if args.output else None,
        css_path=Path(args.css) if args.css else None,
        watermark_text=_resolve_cli_watermark_text(args),
    )

    try:
        output_path = convert_markdown_to_pdf(options)
        print(f"PDF generated: {output_path}")
        return 0
    except Exception as exc:
        print(f"转换失败: {exc}", file=sys.stderr)
        return 1


def _resolve_cli_watermark_text(args: argparse.Namespace) -> str | None:
    if args.watermark_text:
        return args.watermark_text
    if args.watermark:
        return "CONFIDENTIAL"
    return None


if __name__ == "__main__":
    raise SystemExit(main())
