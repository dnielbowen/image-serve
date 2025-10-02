# image-serve

Serve images from your current working directory as a simple web gallery.

Alternatively, you can use a pre-built JSON index denoting filenames to serve 
images deeply nested in a variety of directories (iMessage attachment backup, 
for example).

## Installation

```bash
pip install image-serve
```

## Usage

### Serve Current Directory

Simply run `image-serve` to serve the current directory.

Extra options:

```bash
usage: image-serve [-h] [--host HOST] [--port PORT] [--threads THREADS] [-v]
              [--index-file INDEX_FILE]

Serve images in the current working directory as a simple gallery.

options:
  -h, --help            show this help message and exit
  --host HOST           Host/IP to bind (default: 0.0.0.0)
  --port PORT           Port to bind (default: 8000)
  --threads THREADS     Number of worker threads (default: 8)
  -v, --verbose         Enable verbose server logs (still hides dev server
                        banners)
  --index-file INDEX_FILE
                        Path to JSON index file to serve from (instead of
                        CWD). Use 'generate_index.py' to create one.
```

### Serve from JSON Index

First, generate an index:

```bash
python examples/indexed/generate_index.py /path/to/images --output index.json
```

Then serve:

```bash
image-serve --index-file index.json --port 8000
```

## Options

- `--host HOST`: Host to bind (default: 0.0.0.0)
- `--port PORT`: Port to bind (default: 8000)
- `--threads THREADS`: Number of threads (default: 8)
- `--index-file FILE`: JSON index file to serve from
- `-v, --verbose`: Verbose logging

## License

MIT
