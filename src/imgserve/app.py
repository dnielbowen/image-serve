import os
from flask import Flask, send_file, abort, request
try:
    from .renderer import (
        render_gallery_with_dirs,
        compute_pagination_window,
        format_date_from_timestamp,
    )
except ImportError:
    # Allow running this file directly: `python path/to/imgserve/app.py`
    from renderer import (
        render_gallery_with_dirs,
        compute_pagination_window,
        format_date_from_timestamp,
    )

app = Flask(__name__)

# Image extensions to consider
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.heif')

# Root directory for the gallery (current working directory when the process starts)
ROOT_DIR = os.getcwd()


def list_images_in_directory(directory_path: str, sort_by: str = 'date'):
    if not os.path.isdir(directory_path):
        return []

    entries: list[tuple[str, float]] = []
    for filename in os.listdir(directory_path):
        if not filename.lower().endswith(IMAGE_EXTENSIONS):
            continue
        file_path = os.path.join(directory_path, filename)
        if not os.path.isfile(file_path):
            continue
        if filename.startswith('._'):
            continue
        try:
            mtime = os.path.getmtime(file_path)
        except OSError:
            mtime = float('inf')
        entries.append((filename, mtime))

    if sort_by == 'name':
        entries.sort(key=lambda x: x[0].lower())
    else:  # date
        entries.sort(key=lambda x: float(x[1]), reverse=True)  # newest first
    return entries


@app.route('/')
def index():
    dir_arg = request.args.get('dir', '')
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'date')

    current_dir = os.path.normpath(os.path.join(ROOT_DIR, dir_arg))
    if not current_dir.startswith(ROOT_DIR):
        abort(403, description="Access denied: Directory outside allowed root.")

    if not os.path.isdir(current_dir):
        abort(404, description="Directory not found.")

    image_entries = list_images_in_directory(current_dir, sort_by)
    total_images = len(image_entries)

    pagination = compute_pagination_window(page=page, total_items=total_images)

    tiles = []
    for filename, mtime in image_entries[pagination['start_index']:pagination['end_index']]:
        rel_path = os.path.relpath(current_dir, ROOT_DIR)
        if rel_path == '.':
            img_path = filename
        else:
            img_path = os.path.join(rel_path, filename).replace(os.sep, '/')
        caption = format_date_from_timestamp(mtime)
        tiles.append({
            'href': f"/images/{img_path}",
            'img_src': f"/images/{img_path}",
            'filename': filename,
            'caption': caption,
        })

    subdirs = []
    try:
        for item in os.listdir(current_dir):
            full_path = os.path.join(current_dir, item)
            if os.path.isdir(full_path) and not item.startswith('.'):
                rel_subdir = os.path.relpath(full_path, ROOT_DIR).replace(os.sep, '/')
                subdirs.append((item, rel_subdir))
    except OSError:
        pass

    rel_display = os.path.relpath(current_dir, ROOT_DIR)
    display_path = ROOT_DIR if rel_display == '.' else rel_display
    title = f"CWD Image Gallery: {display_path}"

    return render_gallery_with_dirs(
        title=title,
        page=pagination['page'],
        total_pages=pagination['total_pages'],
        start_page_num=pagination['start_page_num'],
        end_page_num=pagination['end_page_num'],
        tiles=tiles,
        empty_message="No image files found in current directory.",
        subdirs=subdirs,
        current_dir_rel=dir_arg,
        sort_by=sort_by,
    )


@app.route('/images/<path:img_path>')
def serve_image(img_path: str):
    full_path = os.path.normpath(os.path.join(ROOT_DIR, img_path))
    if not full_path.startswith(ROOT_DIR):
        abort(403, description="Access forbidden: File outside allowed root.")

    if not os.path.isfile(full_path):
        abort(404, description="File not found.")

    return send_file(full_path)


if __name__ == "__main__":
    # Lightweight CLI so this file works when run directly
    import argparse
    import logging
    try:
        from waitress import serve as waitress_serve
    except ImportError:
        waitress_serve = None

    parser = argparse.ArgumentParser(
        description="Serve images in the current working directory as a simple gallery.",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("IMGSERVE_HOST", "0.0.0.0"),
        help="Host/IP to bind (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("IMGSERVE_PORT", 8000)),
        help="Port to bind (default: 8000)",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=int(os.environ.get("IMGSERVE_THREADS", 8)),
        help="Number of worker threads (default: 8)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose server logs",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(message)s",
    )
    print(f"Server running at http://{args.host}:{args.port}")
    if waitress_serve is not None:
        logging.getLogger("waitress").setLevel(logging.WARNING)
        logging.getLogger("waitress.access").setLevel(logging.INFO)
        waitress_serve(app, host=args.host, port=args.port, threads=args.threads, ident="imgserve")
    else:
        print("waitress not installed; falling back to Flask's built-in server (for development).")
        app.run(host=args.host, port=args.port)
