# Markdown to PDF (Python)

基于 `markdown + weasyprint` 的 Markdown 转 PDF 命令行工具。

## 功能

- 命令行调用：`md2pdf input.md -o output.pdf`
- 支持自定义 CSS：`--css custom.css`
- 默认提供基础排版样式（标题、列表、代码块、表格）

## 1) 使用 pip 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

运行：

```bash
md2pdf samples/basic.md -o output/basic.pdf
```

## 2) 使用 uv 安装

```bash
uv venv
source .venv/bin/activate
uv pip install -U pip
uv pip install -e .
```

运行：

```bash
md2pdf samples/basic.md -o output/basic.pdf
```

## 3) 使用 conda 安装

```bash
conda create -n md2pdf python=3.11 -y
conda activate md2pdf
pip install -U pip
pip install -e .
```

运行：

```bash
md2pdf samples/basic.md -o output/basic.pdf
```

## Linux 系统依赖（WeasyPrint）

WeasyPrint 在 Linux 上需要系统图形/排版库。常见依赖如下：

- `libcairo2`
- `libpango-1.0-0`
- `libpangocairo-1.0-0`
- `libgdk-pixbuf-2.0-0`
- `libffi-dev`
- `shared-mime-info`
- `fonts-dejavu-core`（建议，避免字体缺失）

Debian/Ubuntu 可参考：

```bash
sudo apt-get update
sudo apt-get install -y \
  libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
  libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info fonts-dejavu-core
```

## CLI 用法

```bash
md2pdf <input.md> [-o output.pdf] [--css custom.css]
```

参数：

- `input`：输入 Markdown 文件路径（必填）
- `-o, --output`：输出 PDF 路径（可选，默认与输入同目录同名 `.pdf`）
- `--css`：自定义 CSS 文件路径（可选）

## 本地验证样例

```bash
md2pdf samples/basic.md -o output/basic.pdf
md2pdf samples/table.md -o output/table.pdf
```
