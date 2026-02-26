# Markdown 转 PDF（Python）

基于 `markdown + weasyprint` 的 Markdown 转 PDF 工具，支持：

- 命令行直接转换文件
- HTTP 服务模式（默认端口 `20706`）
- 自定义 CSS 样式
- 一键打包上传与服务器部署脚本

> English version: `README.md`

## 功能概览

- CLI 直转：`md2pdf input.md -o output.pdf`
- HTTP 模式：`md2pdf --serve --port 20706`
- 健康检查接口：`GET /health`
- 转换接口：`POST /convert`（返回 PDF 二进制）

## 环境要求

- Python `>= 3.10`
- 依赖：
  - `markdown>=3.6`
  - `weasyprint>=62.0`

Linux（尤其服务器）需要 WeasyPrint 的系统库，见下文。

## 安装方式

三种方式任选其一。

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

## CLI 用法

```bash
md2pdf <input.md> [-o output.pdf] [--css custom.css]
md2pdf --serve [--host 127.0.0.1] [--port 20706] [--css custom.css]
```

参数说明：

- `input`：输入 Markdown 文件（非 `--serve` 模式必填）
- `-o, --output`：输出 PDF 路径（默认与输入同名 `.pdf`）
- `--css`：自定义 CSS 路径
- `--serve`：启动 HTTP 服务模式
- `--host`：监听地址，默认 `127.0.0.1`
- `--port`：监听端口，默认 `20706`

### CLI 示例

```bash
md2pdf samples/basic.md -o output/basic.pdf
md2pdf samples/table.md -o output/table.pdf
```

## HTTP 接口

### 启动服务

```bash
md2pdf --serve --port 20706
```

### 健康检查

```bash
curl http://127.0.0.1:20706/health
```

### 转换接口

请求：`POST /convert`

JSON 字段：

- `markdown`（必填，字符串）
- `filename`（可选，下载文件名，默认 `output.pdf`）
- `css_path`（可选，服务端自定义 CSS 文件路径）

示例：

```bash
curl -X POST "http://127.0.0.1:20706/convert" \
  -H "Content-Type: application/json" \
  -d '{"markdown":"# Hello\n\nThis is from HTTP."}' \
  --output output/http.pdf
```

## Linux 系统依赖（WeasyPrint）

Debian/Ubuntu 建议安装：

```bash
sudo apt-get update
sudo apt-get install -y \
  libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
  libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info fonts-dejavu-core
```

如果渲染异常：

- 检查系统字体
- 检查 cairo / pango 等动态库是否完整

## 打包发布

生成 wheel 与源码包：

```bash
python -m build
```

产物在 `dist/`：

- `md2pdf_cli-<version>-py3-none-any.whl`
- `md2pdf_cli-<version>.tar.gz`

## 服务器脚本（scripts/）

项目内置以下脚本：

- `scripts/deploy_ubuntu.sh`
- `scripts/deploy_rhel.sh`
- `scripts/start_http_background.sh`
- `scripts/stop_http_background.sh`
- `upload_bundle_to_server.sh`

### 1) 上传精简部署包（本机执行）

脚本会自动：

- 查找最新 wheel（当前目录或 `dist/`）
- 打包 wheel + 部署/启停脚本
- 上传到服务器目标目录

命令（单参数）：

```bash
# 公钥登录
bash upload_bundle_to_server.sh "root@1.2.3.4:/home/root/md2pdf"

# 密码登录
bash upload_bundle_to_server.sh "root:yourPassword@1.2.3.4:/home/root/md2pdf"
```

说明：

- 密码模式需要本机安装 `sshpass`
- 远端目录不存在会自动创建

### 2) 服务器部署（目标机执行）

```bash
cd /home/root/md2pdf
tar -xzf md2pdf_deploy_bundle_*.tar.gz
sudo bash scripts/deploy_ubuntu.sh
```

RHEL 系统使用：

```bash
sudo bash scripts/deploy_rhel.sh
```

部署脚本行为：

- 默认安装目录：当前目录
- 可选参数 1：自定义安装目录
- 自动查找 wheel：
  - `./md2pdf_cli-*.whl`
  - `./dist/md2pdf_cli-*.whl`

### 3) 后台启动 HTTP 服务

```bash
bash scripts/start_http_background.sh
```

默认配置：

- 项目根目录为安装目录
- `HOST=0.0.0.0`
- `PORT=20706`
- 日志文件：`<项目根>/md2pdf-http.log`
- PID 文件：`<项目根>/md2pdf-http.pid`

可用环境变量覆盖：

- `MD2PDF_HOST`
- `MD2PDF_PORT`
- `MD2PDF_LOG_FILE`
- `MD2PDF_PID_FILE`

示例：

```bash
MD2PDF_PORT=28080 bash scripts/start_http_background.sh
```

### 4) 停止后台服务

```bash
bash scripts/stop_http_background.sh
```

可选参数：

- 参数 1：安装目录（默认当前目录）
- 参数 2：PID 文件（默认 `<安装目录>/md2pdf-http.pid`）

示例：

```bash
bash scripts/stop_http_background.sh "$(pwd)" "$(pwd)/md2pdf-http.pid"
```

## 本地验证

```bash
md2pdf samples/basic.md -o output/basic.pdf
md2pdf samples/table.md -o output/table.pdf
```
