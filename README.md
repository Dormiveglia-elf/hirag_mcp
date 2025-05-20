# HiRAG-MCP

## Quick Start

Make sure uv is installed, if not:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then create the virtual environment and install dependencies using uv as below:
```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

Then create the `.env` file and replace the placeholders with your own values:
```bash
cp .env.example .env
```

Run the script:
```bash
python main.py
```
