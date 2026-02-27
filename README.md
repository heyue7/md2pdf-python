# Markdown to PDF (Python)

A production-oriented Markdown-to-PDF tool powered by `markdown + weasyprint`.

- File-based CLI conversion
- HTTP conversion service (default `20706`)
- Deployment, upload, and background operation scripts

> 中文文档: `README_ZH.md`

## Quick Start

Core scripts (under `scripts/`):

- `scripts/deploy_ubuntu.sh`
- `scripts/deploy_rhel.sh`
- `scripts/start_http_background.sh`
- `scripts/stop_http_background.sh`
- `scripts/convert_with_watermark.sh`

### Install

For servers, use deployment scripts directly:

```bash
# Ubuntu / Debian
sudo bash scripts/deploy_ubuntu.sh

# RHEL family
sudo bash scripts/deploy_rhel.sh
```

### Use

Single-file CLI conversion:

```bash
md2pdf samples/basic.md -o output/basic.pdf
```

Quick watermark conversion (script):

```bash
bash scripts/convert_with_watermark.sh samples/basic.md "INTERNAL"
```

With custom output path:

```bash
bash scripts/convert_with_watermark.sh samples/basic.md "INTERNAL" output/basic_wm_custom.pdf
```

Single-file CLI conversion with watermark:

```bash
md2pdf samples/basic.md -o output/basic_wm.pdf --watermark-text "INTERNAL"
```

Start HTTP service in background:

```bash
bash scripts/start_http_background.sh
```

Stop HTTP service:

```bash
bash scripts/stop_http_background.sh
```

Health check:

```bash
curl http://127.0.0.1:20706/health
```

HTTP conversion call:

```bash
curl -X POST "http://127.0.0.1:20706/convert" \
  -H "Content-Type: application/json" \
  -d '{"markdown":"# Hello\n\nThis is from HTTP."}' \
  --output output/http.pdf
```

HTTP conversion call from a local `.md` file:

```bash
curl -X POST "http://127.0.0.1:20706/convert" \
  -H "Content-Type: application/json" \
  --data "$(python3 -c 'import json, pathlib; p=pathlib.Path("samples/26.43.159.KC-1.1.1.studyGuide.md"); print(json.dumps({"markdown": p.read_text(encoding="utf-8"), "filename": "studyGuide.pdf"}, ensure_ascii=False))')" \
  --output output/studyGuide.pdf
```

HTTP watermark conversion call:

```bash
curl -X POST "http://127.0.0.1:20706/convert-watermark" \
  -H "Content-Type: application/json" \
  -d '{"markdown":"# Watermarked","watermark_text":"TOP SECRET"}' \
  --output output/http_wm.pdf
```

HTTP watermark conversion call from a local `.md` file:

```bash
curl -X POST "http://127.0.0.1:20706/convert-watermark" \
  -H "Content-Type: application/json" \
  --data "$(python3 -c 'import json, pathlib; p=pathlib.Path("samples/26.43.159.KC-1.1.1.studyGuide.md"); print(json.dumps({"markdown": p.read_text(encoding="utf-8"), "watermark_text": "TOP SECRET", "filename": "studyGuide_wm.pdf"}, ensure_ascii=False))')" \
  --output output/studyGuide_wm.pdf
```

### Script parameters and defaults

- `deploy_ubuntu.sh` / `deploy_rhel.sh`
    - default install directory: current directory
    - optional arg1: custom install directory
    - auto wheel discovery: `./md2pdf_cli-*.whl` or `./dist/md2pdf_cli-*.whl`
- `start_http_background.sh`
    - zero-argument startup
    - defaults: `HOST=0.0.0.0`, `PORT=20706`
    - default log: `<project_root>/md2pdf-http.log`
    - default pid: `<project_root>/md2pdf-http.pid`
    - override via env vars:
        - `MD2PDF_HOST`
        - `MD2PDF_PORT`
        - `MD2PDF_LOG_FILE`
        - `MD2PDF_PID_FILE`
- `stop_http_background.sh`
    - optional arg1: install dir (default current directory)
    - optional arg2: pid file (default `<install_dir>/md2pdf-http.pid`)
- `convert_with_watermark.sh`
    - arg1: input markdown file (required)
    - arg2: watermark text (optional, default `CONFIDENTIAL`)
    - arg3: output PDF path (optional, default `<input_stem>_wm.pdf`)

## Server Delivery

Root upload script: `upload_bundle_to_server.sh`

It automatically:

- runs build first (equivalent to `python -m build`)
- finds the latest wheel in current directory or `dist/`
- packages wheel + 5 core scripts
- uploads the bundle to target server directory

Supported single-argument target formats:

- `alias:/remote_dir` (SSH host alias)
- `user@ip:/remote_dir` (SSH key auth)
- `user:password@ip:/remote_dir` (password auth)

Examples:

```bash
# SSH alias
bash upload_bundle_to_server.sh "server-1:/data/md2pdf"

# SSH key
bash upload_bundle_to_server.sh "root@1.2.3.4:/home/root/md2pdf"

# Password
bash upload_bundle_to_server.sh "root:yourPassword@1.2.3.4:/home/root/md2pdf"
```

Notes:

- password mode requires `sshpass` on local machine
- if target directory already exists, script uploads directly (no extra ssh mkdir)
- if target directory is missing, script creates it and retries upload
- to force a specific private key, set `MD2PDF_SSH_KEY=~/.ssh/id_ed25519`

After upload, run on server:

```bash
cd /home/root/md2pdf
tar -xzf md2pdf_deploy_bundle_*.tar.gz
sudo bash scripts/deploy_ubuntu.sh
```

## Runtime Interfaces

### CLI

```bash
md2pdf <input.md> [-o output.pdf] [--css custom.css]
md2pdf <input.md> [-o output.pdf] [--css custom.css] [--watermark] [--watermark-text TEXT]
md2pdf --serve [--host 127.0.0.1] [--port 20706] [--css custom.css]
```

Arguments:

- `input`: Markdown input file (required when not using `--serve`)
- `-o, --output`: output PDF path (defaults to input filename with `.pdf`)
- `--css`: custom CSS file path
- `--watermark`: enable watermark with default text `CONFIDENTIAL`
- `--watermark-text`: custom watermark text (enables watermark)
- `--serve`: run HTTP service mode
- `--host`: bind address, default `127.0.0.1`
- `--port`: bind port, default `20706`

### HTTP API

Start service:

```bash
md2pdf --serve --port 20706
```

Health check:

```bash
curl http://127.0.0.1:20706/health
```

Convert endpoint: `POST /convert`

Watermark convert endpoint: `POST /convert-watermark`

Request JSON fields:

- `markdown` (required, string)
- `filename` (optional, default `output.pdf`)
- `css_path` (optional, server-side CSS path)

Extra field for `/convert-watermark`:

- `watermark_text` (optional, default `CONFIDENTIAL`, recommended to pass explicitly)

Example:

```bash
curl -X POST "http://127.0.0.1:20706/convert" \
  -H "Content-Type: application/json" \
  -d '{"markdown":"# Hello\n\nThis is from HTTP."}' \
  --output output/http.pdf
```

Watermark example:

```bash
curl -X POST "http://127.0.0.1:20706/convert-watermark" \
  -H "Content-Type: application/json" \
  -d '{"markdown":"# Hello\n\nThis is from HTTP.","watermark_text":"CONFIDENTIAL"}' \
  --output output/http_wm.pdf
```

Watermark example (local Markdown file):

```bash
curl -X POST "http://127.0.0.1:20706/convert-watermark" \
  -H "Content-Type: application/json" \
  --data "$(python3 -c 'import json, pathlib; p=pathlib.Path("samples/26.43.159.KC-1.1.1.studyGuide.md"); print(json.dumps({"markdown": p.read_text(encoding="utf-8"), "watermark_text": "CONFIDENTIAL", "filename": "studyGuide_wm.pdf"}, ensure_ascii=False))')" \
  --output output/studyGuide_wm.pdf
```

Example with local Markdown file:

```bash
curl -X POST "http://127.0.0.1:20706/convert" \
  -H "Content-Type: application/json" \
  --data "$(python3 -c 'import json, pathlib; p=pathlib.Path("samples/26.43.159.KC-1.1.1.studyGuide.md"); print(json.dumps({"markdown": p.read_text(encoding="utf-8"), "filename": "studyGuide.pdf"}, ensure_ascii=False))')" \
  --output output/studyGuide.pdf
```

## Local Setup

### pip + venv

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

### uv

```bash
uv venv
source .venv/bin/activate
uv pip install -U pip
uv pip install -e .
```

### conda

```bash
conda create -n md2pdf python=3.11 -y
conda activate md2pdf
pip install -U pip
pip install -e .
```

## Linux Runtime Dependencies (WeasyPrint)

Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y \
  libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
  libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info fonts-dejavu-core
```

## Build Artifacts

```bash
python -m build
```

Artifacts in `dist/`:

- `md2pdf_cli-<version>-py3-none-any.whl`
- `md2pdf_cli-<version>.tar.gz`

## Validation Examples

```bash
md2pdf samples/basic.md -o output/basic.pdf
md2pdf samples/table.md -o output/table.pdf
```
