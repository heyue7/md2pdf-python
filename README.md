# Markdown to PDF (Python)

A Markdown-to-PDF tool based on `markdown + weasyprint`, with support for:

- Direct file conversion via CLI
- HTTP service mode (default port `20706`)
- Custom CSS
- Packaging/upload/deployment helper scripts

> Chinese version: `README_ZH.md`

## Features

- CLI conversion: `md2pdf input.md -o output.pdf`
- HTTP mode: `md2pdf --serve --port 20706`
- Health endpoint: `GET /health`
- Conversion endpoint: `POST /convert` (returns PDF bytes)

## Requirements

- Python `>= 3.10`
- Python dependencies:
  - `markdown>=3.6`
  - `weasyprint>=62.0`

For Linux servers, install system libraries required by WeasyPrint (see below).

## Installation

Choose one setup flow.

### 1) pip + venv

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

### 2) uv

```bash
uv venv
source .venv/bin/activate
uv pip install -U pip
uv pip install -e .
```

### 3) conda

```bash
conda create -n md2pdf python=3.11 -y
conda activate md2pdf
pip install -U pip
pip install -e .
```

## CLI Usage

```bash
md2pdf <input.md> [-o output.pdf] [--css custom.css]
md2pdf --serve [--host 127.0.0.1] [--port 20706] [--css custom.css]
```

Arguments:

- `input`: input Markdown file (required when not using `--serve`)
- `-o, --output`: output PDF path (defaults to input name with `.pdf`)
- `--css`: custom CSS file path
- `--serve`: run HTTP service mode
- `--host`: bind host, default `127.0.0.1`
- `--port`: bind port, default `20706`

### CLI Examples

```bash
md2pdf samples/basic.md -o output/basic.pdf
md2pdf samples/table.md -o output/table.pdf
```

## HTTP API

### Start service

```bash
md2pdf --serve --port 20706
```

### Health check

```bash
curl http://127.0.0.1:20706/health
```

### Convert endpoint

Request: `POST /convert`

JSON fields:

- `markdown` (required, string)
- `filename` (optional, default `output.pdf`)
- `css_path` (optional, custom CSS path on server)

Example:

```bash
curl -X POST "http://127.0.0.1:20706/convert" \
  -H "Content-Type: application/json" \
  -d '{"markdown":"# Hello\n\nThis is from HTTP."}' \
  --output output/http.pdf
```

## Linux System Dependencies (WeasyPrint)

Recommended packages on Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y \
  libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
  libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info fonts-dejavu-core
```

If rendering fails, check fonts and dynamic libraries (`cairo`, `pango`, etc.).

## Build

Create wheel and source distribution:

```bash
python -m build
```

Artifacts in `dist/`:

- `md2pdf_cli-<version>-py3-none-any.whl`
- `md2pdf_cli-<version>.tar.gz`

## Deployment Scripts

Included scripts:

- `scripts/deploy_ubuntu.sh`
- `scripts/deploy_rhel.sh`
- `scripts/start_http_background.sh`
- `scripts/stop_http_background.sh`
- `upload_bundle_to_server.sh`

### 1) Upload minimal deployment bundle (local machine)

This script automatically:

- finds the latest wheel in current directory or `dist/`
- packages the wheel and deployment scripts
- uploads bundle to target server path

Single argument format:

```bash
# SSH key auth
bash upload_bundle_to_server.sh "root@1.2.3.4:/home/root/md2pdf"

# Password auth
bash upload_bundle_to_server.sh "root:yourPassword@1.2.3.4:/home/root/md2pdf"
```

Notes:

- Password mode requires `sshpass` on local machine
- Target directory is created automatically if missing

### 2) Deploy on server

```bash
cd /home/root/md2pdf
tar -xzf md2pdf_deploy_bundle_*.tar.gz
sudo bash scripts/deploy_ubuntu.sh
```

For RHEL family:

```bash
sudo bash scripts/deploy_rhel.sh
```

Deploy script behavior:

- default install directory: current directory
- optional argument 1: custom install directory
- wheel auto-discovery:
  - `./md2pdf_cli-*.whl`
  - `./dist/md2pdf_cli-*.whl`

### 3) Start HTTP service in background

```bash
bash scripts/start_http_background.sh
```

Defaults:

- install root: project root directory
- `HOST=0.0.0.0`
- `PORT=20706`
- log file: `<project_root>/md2pdf-http.log`
- pid file: `<project_root>/md2pdf-http.pid`

Override with env vars:

- `MD2PDF_HOST`
- `MD2PDF_PORT`
- `MD2PDF_LOG_FILE`
- `MD2PDF_PID_FILE`

Example:

```bash
MD2PDF_PORT=28080 bash scripts/start_http_background.sh
```

### 4) Stop background service

```bash
bash scripts/stop_http_background.sh
```

Optional args:

- arg 1: install directory (default current directory)
- arg 2: pid file path (default `<install_dir>/md2pdf-http.pid`)

Example:

```bash
bash scripts/stop_http_background.sh "$(pwd)" "$(pwd)/md2pdf-http.pid"
```

## Local Validation

```bash
md2pdf samples/basic.md -o output/basic.pdf
md2pdf samples/table.md -o output/table.pdf
```
