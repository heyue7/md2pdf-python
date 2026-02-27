# Markdown 转 PDF（Python）

面向生产部署的 Markdown 转 PDF 工具，基于 `markdown + weasyprint`。

- 文件级 CLI 转换
- HTTP 转换服务（默认 `20706`）
- 完整的部署、上传与后台运维脚本

> English: `README.md`

## 快速启动

核心脚本（位于 `scripts/`）：

- `scripts/deploy_ubuntu.sh`
- `scripts/deploy_rhel.sh`
- `scripts/start_http_background.sh`
- `scripts/stop_http_background.sh`
- `scripts/convert_with_watermark.sh`

### 安装

服务器推荐直接使用部署脚本：

```bash
# Ubuntu / Debian
sudo bash scripts/deploy_ubuntu.sh

# RHEL 系
sudo bash scripts/deploy_rhel.sh
```

### 使用

CLI 单文件转换：

```bash
md2pdf samples/basic.md -o output/basic.pdf
```

快捷水印转换（脚本）：

```bash
bash scripts/convert_with_watermark.sh samples/basic.md "INTERNAL"
```

可选输出路径：

```bash
bash scripts/convert_with_watermark.sh samples/basic.md "INTERNAL" output/basic_wm_custom.pdf
```

CLI 单文件转换（带水印）：

```bash
md2pdf samples/basic.md -o output/basic_wm.pdf --watermark-text "INTERNAL"
```

后台启动 HTTP 服务：

```bash
bash scripts/start_http_background.sh
```

健康检查：

```bash
curl http://127.0.0.1:20706/health
```

调用 HTTP 转换：

```bash
curl -X POST "http://127.0.0.1:20706/convert" \
  -H "Content-Type: application/json" \
  -d '{"markdown":"# Hello\n\nThis is from HTTP."}' \
  --output output/http.pdf
```

调用 HTTP 转换（读取本地 `.md` 文件）：

```bash
curl -X POST "http://127.0.0.1:20706/convert" \
  -H "Content-Type: application/json" \
  --data "$(python3 -c 'import json, pathlib; p=pathlib.Path("samples/26.43.159.KC-1.1.1.studyGuide.md"); print(json.dumps({"markdown": p.read_text(encoding="utf-8"), "filename": "studyGuide.pdf"}, ensure_ascii=False))')" \
  --output output/studyGuide.pdf
```

调用 HTTP 水印转换：

```bash
curl -X POST "http://127.0.0.1:20706/convert-watermark" \
  -H "Content-Type: application/json" \
  -d '{"markdown":"# Watermarked","watermark_text":"TOP SECRET"}' \
  --output output/http_wm.pdf
```

调用 HTTP 水印转换（读取本地 `.md` 文件）：

```bash
curl -X POST "http://127.0.0.1:20706/convert-watermark" \
  -H "Content-Type: application/json" \
  --data "$(python3 -c 'import json, pathlib; p=pathlib.Path("samples/26.43.159.KC-1.1.1.studyGuide.md"); print(json.dumps({"markdown": p.read_text(encoding="utf-8"), "watermark_text": "TOP SECRET", "filename": "studyGuide_wm.pdf"}, ensure_ascii=False))')" \
  --output output/studyGuide_wm.pdf
```

停止 HTTP 服务：

```bash
bash scripts/stop_http_background.sh
```

### 脚本参数与默认值

- `deploy_ubuntu.sh` / `deploy_rhel.sh`
    - 默认安装目录：当前目录
    - 可选参数 1：自定义安装目录
    - 自动查找 wheel：`./md2pdf_cli-*.whl` 或 `./dist/md2pdf_cli-*.whl`
- `start_http_background.sh`
    - 无参数启动
    - 默认 `HOST=0.0.0.0`、`PORT=20706`
    - 默认日志：`<项目根>/md2pdf-http.log`
    - 默认 PID：`<项目根>/md2pdf-http.pid`
    - 可用环境变量覆盖：
        - `MD2PDF_HOST`
        - `MD2PDF_PORT`
        - `MD2PDF_LOG_FILE`
        - `MD2PDF_PID_FILE`
- `stop_http_background.sh`
    - 可选参数 1：安装目录（默认当前目录）
    - 可选参数 2：PID 文件（默认 `<安装目录>/md2pdf-http.pid`）
- `convert_with_watermark.sh`
    - 参数 1：输入 markdown 文件（必填）
    - 参数 2：水印文字（可选，默认 `CONFIDENTIAL`）
    - 参数 3：输出 PDF（可选，默认 `<输入文件名>_wm.pdf`）

## 发布到服务器

根目录上传脚本：`upload_bundle_to_server.sh`

该脚本会自动：

- 发现最新 wheel（当前目录或 `dist/`）
- 打包 wheel + 4 个核心脚本
- 打包 wheel + 5 个核心脚本
- 上传到目标服务器目录

支持的单参数目标格式：

- `alias:/remote_dir`（SSH Host 昵称）
- `user@ip:/remote_dir`（公钥认证）
- `user:password@ip:/remote_dir`（密码认证）

示例：

```bash
# SSH 配置昵称
bash upload_bundle_to_server.sh "server-1:/data/md2pdf"

# 公钥登录
bash upload_bundle_to_server.sh "root@1.2.3.4:/home/root/md2pdf"

# 密码登录
bash upload_bundle_to_server.sh "root:yourPassword@1.2.3.4:/home/root/md2pdf"
```

注意：

- 密码模式依赖本机 `sshpass`
- 若远端目录已存在，脚本直接上传（不额外执行 ssh mkdir）
- 若远端目录不存在，脚本会自动创建后重试上传
- 如需指定私钥文件，可设置环境变量：`MD2PDF_SSH_KEY=~/.ssh/id_ed25519`

上传后在服务器执行：

```bash
cd /home/root/md2pdf
tar -xzf md2pdf_deploy_bundle_*.tar.gz
sudo bash scripts/deploy_ubuntu.sh
```

## 功能接口

### CLI

```bash
md2pdf <input.md> [-o output.pdf] [--css custom.css]
md2pdf <input.md> [-o output.pdf] [--css custom.css] [--watermark] [--watermark-text TEXT]
md2pdf --serve [--host 127.0.0.1] [--port 20706] [--css custom.css]
```

参数说明：

- `input`：输入 Markdown 文件（非 `--serve` 模式必填）
- `-o, --output`：输出 PDF 路径（默认与输入同名 `.pdf`）
- `--css`：自定义 CSS 文件路径
- `--watermark`：开启水印（默认文字 `CONFIDENTIAL`）
- `--watermark-text`：自定义水印文字（设置后即启用水印）
- `--serve`：启动 HTTP 服务模式
- `--host`：监听地址，默认 `127.0.0.1`
- `--port`：监听端口，默认 `20706`

### HTTP API

启动服务：

```bash
md2pdf --serve --port 20706
```

健康检查：

```bash
curl http://127.0.0.1:20706/health
```

转换端点：`POST /convert`

水印转换端点：`POST /convert-watermark`

请求 JSON 字段：

- `markdown`（必填，字符串）
- `filename`（可选，默认 `output.pdf`）
- `css_path`（可选，服务端 CSS 路径）

`/convert-watermark` 额外字段：

- `watermark_text`（可选，默认 `CONFIDENTIAL`，建议显式传入）

示例：

```bash
curl -X POST "http://127.0.0.1:20706/convert" \
  -H "Content-Type: application/json" \
  -d '{"markdown":"# Hello\n\nThis is from HTTP."}' \
  --output output/http.pdf
```

水印示例：

```bash
curl -X POST "http://127.0.0.1:20706/convert-watermark" \
  -H "Content-Type: application/json" \
  -d '{"markdown":"# Hello\n\nThis is from HTTP.","watermark_text":"CONFIDENTIAL"}' \
  --output output/http_wm.pdf
```

水印示例（本地 Markdown 文件）：

```bash
curl -X POST "http://127.0.0.1:20706/convert-watermark" \
  -H "Content-Type: application/json" \
  --data "$(python3 -c 'import json, pathlib; p=pathlib.Path("samples/26.43.159.KC-1.1.1.studyGuide.md"); print(json.dumps({"markdown": p.read_text(encoding="utf-8"), "watermark_text": "CONFIDENTIAL", "filename": "studyGuide_wm.pdf"}, ensure_ascii=False))')" \
  --output output/studyGuide_wm.pdf
```

## 本地开发安装

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

## Linux 运行依赖（WeasyPrint）

Debian/Ubuntu：

```bash
sudo apt-get update
sudo apt-get install -y \
  libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
  libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info fonts-dejavu-core
```

## 构建产物

```bash
python -m build
```

产物在 `dist/`：

- `md2pdf_cli-<version>-py3-none-any.whl`
- `md2pdf_cli-<version>.tar.gz`

## 验证示例

```bash
md2pdf samples/basic.md -o output/basic.pdf
md2pdf samples/table.md -o output/table.pdf
```
