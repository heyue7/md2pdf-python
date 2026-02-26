# AGENTS.md
Reply in Chinese.

Guidance for agentic coding tools in this repository.

## Project Overview
- Type: Python CLI package.
- Purpose: convert Markdown to PDF via `markdown` + `weasyprint`.
- Python: `>=3.10`.
- Entry point: `md2pdf = md2pdf.cli:main`.
- Core files: `md2pdf/cli.py`, `md2pdf/converter.py`, `md2pdf/default.css`.
- Source of truth: `pyproject.toml`, `README.md`.

## Setup Commands
Use one environment flow.

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

## Build / Run / Lint / Test

### Run CLI
```bash
md2pdf <input.md> [-o output.pdf] [--css custom.css]
```

Examples:
```bash
md2pdf samples/basic.md -o output/basic.pdf
md2pdf samples/table.md -o output/table.pdf
```

### Build
Local editable install:
```bash
pip install -e .
```
Optional distribution build (`build` package required):
```bash
python -m build
```

### Lint
No linter is configured in `pyproject.toml`.
If available locally:
```bash
ruff check .
```

### Test
Current repository state:
- No tests are present.
- No `pytest` or `unittest` configuration detected.

If tests are added later:
```bash
pytest
```
Single test file pattern:
```bash
pytest path/to/test_file.py
```
Single test case pattern:
```bash
pytest path/to/test_file.py::test_name
```

## Platform Notes (WeasyPrint)
Linux needs native libs for rendering.
Debian/Ubuntu packages from README:
```bash
sudo apt-get update
sudo apt-get install -y \
  libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
  libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info fonts-dejavu-core
```
Operational cautions:
- macOS may require Homebrew native libs if rendering fails.
- If dynamic library loading fails, inspect library path settings.

## Code Style Guidelines
Inferred from existing code; preserve these conventions.

### Imports
- Put `from __future__ import annotations` at module top.
- Group imports: stdlib, third-party, local.
- Keep one blank line between groups.

### Formatting
- Follow PEP 8, 4-space indentation.
- Keep modules single-purpose (`cli.py`, `converter.py`).
- Use two blank lines between top-level declarations.

### Typing
- Type all function parameters and return values.
- Prefer Python 3.10 union style: `Path | None`.
- Prefer built-in generics: `list[str]`.
- Use `@dataclass(slots=True)` for option containers.

### Naming
- Variables/functions: `snake_case`.
- Classes: `PascalCase`.
- Internal helpers: `_leading_underscore`.
- Use descriptive action names, e.g. `convert_markdown_to_pdf`.

### Paths and IO
- Use `pathlib.Path` for path operations.
- Normalize user paths with `.expanduser().resolve()`.
- Create output parent dirs before writing.
- Use explicit UTF-8 encoding for text reads.

### Error Handling
- Raise specific exceptions for invalid input paths.
- In CLI, catch top-level exceptions and return non-zero exit code.
- Print errors to `stderr`.
- Keep messages actionable.

### CLI Structure
- Keep parser construction in `build_parser()`.
- Keep `main()` returning `int` exit code.
- Use `raise SystemExit(main())` in module guard.
- Preserve option style (`-o/--output`, `--css`).

### Rendering Safety
- Escape untrusted values inserted into HTML (`html.escape`).
- Keep HTML wrapper deterministic.
- Load packaged CSS via `importlib.resources`.

## Agent Workflow Expectations
- Make minimal, targeted edits.
- Match existing patterns before introducing new structure.
- Do not assume tests exist; verify repo state first.
- If CLI behavior changes, update `README.md`.
- For conversion logic changes, run sample conversions.

## Cursor / Copilot Rules Status
Checked locations:
- `.cursorrules`: not present
- `.cursor/rules/`: not present
- `.github/copilot-instructions.md`: not present

If these files are added later, treat them as higher-priority instructions and merge relevant rules into this guide.
