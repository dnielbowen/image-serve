# imgserve

A tiny Flask-based gallery server that serves images from your current working directory. Includes a production-ready CLI powered by Waitress and a minimal HTML UI.

## Quickstart

```bash
pip install .
imgserve --host 0.0.0.0 --port 8000
```

Browse: http://localhost:8000

## Options

- `--host` (default `0.0.0.0`)
- `--port` (default `8000`)
- `--threads` (default `8`)
- `-v`/`--verbose` to show more server logs (access logs are always visible)

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
imgserve -v
```

## License

MIT
