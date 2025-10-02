import os
import logging
from flask import Flask, send_file, abort, request

logger = logging.getLogger(__name__)
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

# Image extensions to consider
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.heif')


def create_app(index_file=None):
    """Create and configure the Flask app."""
    app = Flask(__name__)

    if index_file:
        # Index mode: load from JSON index file
        import json
        try:
            with open(index_file, 'r') as f:
                all_indexed_images = json.load(f)
            # Sort by mtime descending (newest first)
            all_indexed_images.sort(key=lambda x: float(x.get('mtime', 0)), reverse=True)
            logger.info(f"Loaded {len(all_indexed_images)} images from index '{index_file}'.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading index file '{index_file}': {e}")
            all_indexed_images = []

        # Store in app config for routes to access
        app.config['INDEX_MODE'] = True
        app.config['ALL_INDEXED_IMAGES'] = all_indexed_images
        app.config['ROOT_DIR'] = None  # Not used in index mode
    else:
        # CWD mode: serve from current working directory
        app.config['INDEX_MODE'] = False
        app.config['ALL_INDEXED_IMAGES'] = []
        app.config['ROOT_DIR'] = os.getcwd()

    @app.route('/')
    def index():
        if app.config['INDEX_MODE']:
            # Index mode: serve from pre-loaded index
            total_images = len(app.config['ALL_INDEXED_IMAGES'])
            logger.info(f"Index mode: {total_images} images from index file")
            page = request.args.get('page', 1, type=int)

            pagination = compute_pagination_window(page=page, total_items=total_images)

            tiles = []
            for i in range(pagination['start_index'], min(pagination['end_index'], total_images)):
                image_data = app.config['ALL_INDEXED_IMAGES'][i]
                filename = os.path.basename(image_data['path'])
                caption = format_date_from_timestamp(image_data.get('mtime', 0))
                tiles.append({
                    'href': f"/images/{i}",
                    'img_src': f"/images/{i}",
                    'filename': filename,
                    'caption': caption,
                })

            from .renderer import render_gallery
            return render_gallery(
                title="Indexed Image Gallery",
                page=pagination['page'],
                total_pages=pagination['total_pages'],
                start_page_num=pagination['start_page_num'],
                end_page_num=pagination['end_page_num'],
                tiles=tiles,
                empty_message="No image files found in the index.",
            )
        else:
            # CWD mode: original logic
            dir_arg = request.args.get('dir', '')
            page = request.args.get('page', 1, type=int)
            sort_by = request.args.get('sort', 'name')

            current_dir = os.path.normpath(os.path.join(app.config['ROOT_DIR'], dir_arg))
            if not current_dir.startswith(app.config['ROOT_DIR']):
                abort(403, description="Access denied: Directory outside allowed root.")

            if not os.path.isdir(current_dir):
                abort(404, description="Directory not found.")

            image_entries = list_images_in_directory(current_dir, sort_by)
            total_images = len(image_entries)

            # Log directory statistics
            rel_display = os.path.relpath(current_dir, app.config['ROOT_DIR'])
            display_path = app.config['ROOT_DIR'] if rel_display == '.' else rel_display
            logger.info(f"Directory: {display_path} ({total_images} images)")

            # Log subdirectory statistics
            subdir_stats = []
            try:
                for item in os.listdir(current_dir):
                    full_path = os.path.join(current_dir, item)
                    if os.path.isdir(full_path) and not item.startswith('.'):
                        subdir_images = len(list_images_in_directory(full_path, 'date'))
                        subdir_stats.append(f"{item}({subdir_images})")
            except OSError:
                pass

            if subdir_stats:
                logger.info(f"Subdirectories: {', '.join(subdir_stats)}")

            pagination = compute_pagination_window(page=page, total_items=total_images)

            tiles = []
            for filename, mtime in image_entries[pagination['start_index']:pagination['end_index']]:
                rel_path = os.path.relpath(current_dir, app.config['ROOT_DIR'])
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
                        rel_subdir = os.path.relpath(full_path, app.config['ROOT_DIR']).replace(os.sep, '/')
                        subdirs.append((item, rel_subdir))
            except OSError:
                pass

            rel_display = os.path.relpath(current_dir, app.config['ROOT_DIR'])
            display_path = app.config['ROOT_DIR'] if rel_display == '.' else rel_display
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
        if app.config['INDEX_MODE']:
            # Index mode: serve by index
            try:
                image_index = int(img_path)
                if not (0 <= image_index < len(app.config['ALL_INDEXED_IMAGES'])):
                    abort(404, description="Image not found in index.")
                image_data = app.config['ALL_INDEXED_IMAGES'][image_index]
                full_path = image_data['path']
                # Security check: ensure path exists and is file
                if not os.path.isfile(full_path):
                    abort(404, description="File not found on disk.")
                return send_file(full_path)
            except ValueError:
                abort(400, description="Invalid image index.")
        else:
            # CWD mode: original logic
            full_path = os.path.normpath(os.path.join(app.config['ROOT_DIR'], img_path))
            if not full_path.startswith(app.config['ROOT_DIR']):
                abort(403, description="Access forbidden: File outside allowed root.")
            if not os.path.isfile(full_path):
                abort(404, description="File not found.")
            return send_file(full_path)

    return app


def list_images_in_directory(directory_path: str, sort_by: str = 'name'):
    """Return a sorted list of (filename, mtime) for image files in the directory.

    By default, sorted alphabetically by filename.
    """
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


# Create default app for backward compatibility
app = create_app()


if __name__ == "__main__":
    # Simple direct run with defaults (CWD mode, no CLI)
    import logging
    try:
        from waitress import serve
        logging.basicConfig(level=logging.WARNING, format="%(message)s")
        logging.getLogger("waitress").setLevel(logging.WARNING)
        logging.getLogger("waitress.access").setLevel(logging.WARNING)
        # Disable app logs by default (quiet mode)
        logging.getLogger("imgserve").setLevel(logging.WARNING)
        print("Server running at http://0.0.0.0:8000")
        serve(app, host="0.0.0.0", port=8000, threads=8, ident="imgserve")
    except ImportError:
        print("waitress not installed; falling back to Flask's built-in server (for development).")
        print("Server running at http://127.0.0.1:5000")
        app.run(host="127.0.0.1", port=5000)
