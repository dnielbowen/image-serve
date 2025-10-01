import os
from flask import Flask, send_from_directory, abort, request
from gallery_renderer import (
    render_gallery,
    compute_pagination_window,
    format_date_from_timestamp,
)

app = Flask(__name__)

# Image extensions to consider
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.heif')

# Serve from current working directory when the process starts
CWD_IMAGES_DIR = os.getcwd()


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
    page = request.args.get('page', 1, type=int)

    # Snapshot the current directory contents per request to reflect changes
    image_entries = list_images_in_directory(CWD_IMAGES_DIR)
    total_images = len(image_entries)

    pagination = compute_pagination_window(page=page, total_items=total_images)

    # Build tiles for the current slice
    tiles = []
    for filename, mtime in image_entries[pagination['start_index']:pagination['end_index']]:
        caption = format_date_from_timestamp(mtime)
        tiles.append({
            'href': f"/images/{filename}",
            'img_src': f"/images/{filename}",
            'caption': caption,
        })

    return render_gallery(
        title=f"CWD Image Gallery: {os.path.basename(CWD_IMAGES_DIR) or CWD_IMAGES_DIR}",
        page=pagination['page'],
        total_pages=pagination['total_pages'],
        start_page_num=pagination['start_page_num'],
        end_page_num=pagination['end_page_num'],
        tiles=tiles,
        empty_message="No image files found in current directory.",
    )


@app.route('/images/<path:filename>')
def serve_image(filename: str):
    # Only serve files from the working directory
    safe_dir = os.path.abspath(CWD_IMAGES_DIR)
    try:
        # send_from_directory validates traversal attempts
        return send_from_directory(safe_dir, filename)
    except FileNotFoundError:
        abort(404)


if __name__ == '__main__':
    app.run(debug=True)
