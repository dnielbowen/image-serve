import os
import argparse
from flask import Flask, send_file, abort, request
from gallery_renderer import (
    render_gallery_with_dirs,
    compute_pagination_window,
    format_date_from_timestamp,
)

app = Flask(__name__)

# Image extensions to consider
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.heif')

# Root directory for the gallery (current working directory when the process starts)
ROOT_DIR = os.getcwd()


def list_images_in_directory(directory_path: str):
    """Return a sorted list of (filename, mtime) for image files in the directory.
    Sorted by mtime ascending (earliest first).
    """
    if not os.path.isdir(directory_path):
        return []

    entries = []
    for filename in os.listdir(directory_path):
        if not filename.lower().endswith(IMAGE_EXTENSIONS):
            continue
        file_path = os.path.join(directory_path, filename)
        if not os.path.isfile(file_path):
            continue
        if filename.startswith('._'):
            # skip AppleDouble files
            continue
        try:
            mtime = os.path.getmtime(file_path)
        except OSError:
            mtime = float('inf')
        entries.append((filename, mtime))

    # Sort by mtime
    entries.sort(key=lambda x: float(x[1]))
    return entries


@app.route('/')
def index():
    # Get directory parameter, default to root
    dir_arg = request.args.get('dir', '')
    page = request.args.get('page', 1, type=int)

    # Resolve and secure the current directory
    current_dir = os.path.normpath(os.path.join(ROOT_DIR, dir_arg))
    if not current_dir.startswith(ROOT_DIR):
        abort(403, description="Access denied: Directory outside allowed root.")

    if not os.path.isdir(current_dir):
        abort(404, description="Directory not found.")

    # Snapshot the current directory contents per request to reflect changes
    image_entries = list_images_in_directory(current_dir)
    total_images = len(image_entries)

    pagination = compute_pagination_window(page=page, total_items=total_images)

    # Build tiles for the current slice
    tiles = []
    for filename, mtime in image_entries[pagination['start_index']:pagination['end_index']]:
        # Images are served relative to ROOT_DIR, so href should include the full relative path
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

    # Get subdirectories for navigation
    subdirs = []
    try:
        for item in os.listdir(current_dir):
            full_path = os.path.join(current_dir, item)
            if os.path.isdir(full_path) and not item.startswith('.'):
                rel_subdir = os.path.relpath(full_path, ROOT_DIR).replace(os.sep, '/')
                subdirs.append((item, rel_subdir))
    except OSError:
        pass  # Ignore if can't list

    # Create title
    rel_display = os.path.relpath(current_dir, ROOT_DIR)
    if rel_display == '.':
        display_path = ROOT_DIR
    else:
        display_path = rel_display
    title = f"CWD Image Gallery: {display_path}"

    # Render gallery with subdirs at bottom
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
    )


@app.route('/images/<path:img_path>')
def serve_image(img_path: str):
    # Resolve the full path and check security
    full_path = os.path.normpath(os.path.join(ROOT_DIR, img_path))
    if not full_path.startswith(ROOT_DIR):
        abort(403, description="Access forbidden: File outside allowed root.")

    if not os.path.isfile(full_path):
        abort(404, description="File not found.")

    try:
        return send_file(full_path)
    except Exception as e:
        print(f"Error serving file '{full_path}': {e}")
        abort(500, description="Internal server error when serving image.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the CWD image gallery server.')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on (default: 8000)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    args = parser.parse_args()
    app.run(debug=True, host=args.host, port=args.port)
