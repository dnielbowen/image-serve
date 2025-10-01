import os
from datetime import datetime
from flask import render_template_string

# Shared display configuration
IMAGES_PER_PAGE = 300
PAGINATION_LINKS_TO_SHOW = 10


def format_date_from_timestamp(timestamp: float) -> str:
    """Return a human-friendly date label like 'Aug 23, 2022'."""
    try:
        dt_object = datetime.fromtimestamp(float(timestamp))
        return dt_object.strftime("%b %d, %Y")
    except Exception:
        return "Date N/A"


def compute_pagination_window(page: int, total_items: int, per_page: int = IMAGES_PER_PAGE,
                              links_to_show: int = PAGINATION_LINKS_TO_SHOW):
    """Compute corrected page bounds, item slice, and numbered pagination window.

    Returns a dict with keys:
      page, total_pages, start_index, end_index, start_page_num, end_page_num
    """
    if per_page <= 0:
        per_page = IMAGES_PER_PAGE

    total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 0

    # Normalize page within valid range
    if page is None or page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    elif total_pages == 0:
        page = 1

    start_index = (page - 1) * per_page if total_pages > 0 else 0
    end_index = start_index + per_page if total_pages > 0 else 0

    # Numbered pagination range
    half_links = links_to_show // 2
    start_page_num = max(1, page - half_links)
    end_page_num = min(total_pages, page + (links_to_show - 1 - half_links))

    if end_page_num == total_pages:
        start_page_num = max(1, total_pages - links_to_show + 1)

    if start_page_num == 1:
        end_page_num = min(total_pages, links_to_show)

    if total_pages == 0:
        start_page_num, end_page_num = 0, 0
    elif start_page_num > end_page_num:
        start_page_num, end_page_num = 1, total_pages

    return {
        "page": page,
        "total_pages": total_pages,
        "start_index": start_index,
        "end_index": end_index,
        "start_page_num": start_page_num,
        "end_page_num": end_page_num,
    }


def render_gallery(title: str,
                   page: int,
                   total_pages: int,
                   start_page_num: int,
                   end_page_num: int,
                   tiles: list[dict],
                   empty_message: str = "No image files found."):
    """
    Render a simple tiled gallery.

    tiles: list of { 'href': str, 'img_src': str, 'caption': str }
    """
    html_content = f"""
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
        <title>{title} (Page {page} of {total_pages})</title>
        <style>
            body {{
                font-family: sans-serif;
                margin: 5px;
                background-color: #f0f0f0;
            }}
            h1 {{
                text-align: center;
                color: #333;
            }}
            .gallery-container {{
                display: flex;
                flex-wrap: wrap;
                gap: 4px;
                justify-content: center;
                padding: 5px;
            }}
            .image-tile {{
                border: 1px solid #ddd;
                padding: 5px;
                background-color: white;
                box-shadow: 3px 3px 8px rgba(0,0,0,0.15);
                text-align: center;
                border-radius: 8px;
                transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
            }}
            .image-tile:hover {{
                transform: translateY(-5px);
                box-shadow: 5px 5px 15px rgba(0,0,0,0.2);
            }}
            .image-tile img {{
                width: 150px;
                height: 150px;
                object-fit: cover;
                display: block;
                margin: 0 auto;
                border-radius: 4px;
            }}
            .image-tile a {{
                text-decoration: none;
                color: #333;
                font-size: 0.9em;
                display: block;
                font-weight: bold;
            }}
            .image-tile a:hover {{
                color: #007bff;
            }}
            .image-filename {{
                font-size: 0.8em;
                color: #555;
                margin-top: 2px;
                display: block;
                font-weight: normal;
            }}
            .image-date {{
                font-size: 0.75em;
                color: #888;
                margin-top: 2px;
                display: block;
                font-weight: normal;
            }}
            .no-images {{
                text-align: center;
                color: #666;
                font-style: italic;
                margin-top: 50px;
            }}
            .pagination {{
                text-align: center;
                margin-top: 30px;
                margin-bottom: 30px;
            }}
            .pagination a, .pagination span {{
                display: inline-block;
                padding: 10px 15px;
                margin: 0 3px;
                border: 1px solid #007bff;
                border-radius: 5px;
                text-decoration: none;
                color: #007bff;
                background-color: #fff;
                transition: background-color 0.3s, color 0.3s;
            }}
            .pagination a:hover {{
                background-color: #007bff;
                color: #fff;
            }}
            .pagination span.current-page {{
                background-color: #007bff;
                color: #fff;
                font-weight: bold;
                border-color: #007bff;
            }}
            .pagination span.disabled {{
                border: 1px solid #ccc;
                color: #ccc;
                background-color: #f9f9f9;
                cursor: not-allowed;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <div class="gallery-container">
    """

    if not tiles:
        html_content += f"<p class='no-images'>{empty_message}</p>"
    else:
        for tile in tiles:
            href = tile.get("href", "#")
            img_src = tile.get("img_src", "")
            filename = tile.get("filename", "")
            caption = tile.get("caption", "")
            html_content += f"""
            <div class="image-tile">
                <a href="{href}" target="_blank">
                    <img src="{img_src}" alt="image">
                    <p class="image-filename">{filename}</p>
                    <p class="image-date">{caption}</p>
                </a>
            </div>
            """

    html_content += """
        </div>
        <div class="pagination">
    """

    # Previous
    if page > 1:
        html_content += f"<a href='/?page={page - 1}'>&laquo; Previous</a>"
    else:
        html_content += "<span class='disabled'>&laquo; Previous</span>"

    # Numbered links
    if total_pages > 0:
        for p_num in range(start_page_num, end_page_num + 1):
            if p_num == page:
                html_content += f"<span class='current-page'>{p_num}</span>"
            else:
                html_content += f"<a href='/?page={p_num}'>{p_num}</a>"

    # Next
    if page < total_pages:
        html_content += f"<a href='/?page={page + 1}'>Next &raquo;</a>"
    else:
        html_content += "<span class='disabled'>Next &raquo;</span>"

    html_content += """
        </div>
    </body>
    </html>
    """

    return render_template_string(html_content)


def render_gallery_with_dirs(title: str,
                             page: int,
                             total_pages: int,
                             start_page_num: int,
                             end_page_num: int,
                             tiles: list[dict],
                             empty_message: str = "No image files found.",
                             subdirs: list[tuple[str, str]] = None,
                             current_dir_rel: str = ""):
    """
    Render a tiled gallery with subdirectory navigation at the bottom.

    subdirs: list of (display_name, relative_path) for subdirectories
    current_dir_rel: the current directory relative to root, for pagination links
    """
    if subdirs is None:
        subdirs = []

    html_content = f"""
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
        <title>{title} (Page {page} of {total_pages})</title>
        <style>
            body {{
                font-family: sans-serif;
                margin: 5px;
                background-color: #f0f0f0;
            }}
            h1 {{
                text-align: center;
                color: #333;
            }}
            .gallery-container {{
                display: flex;
                flex-wrap: wrap;
                gap: 4px;
                justify-content: center;
                padding: 5px;
            }}
            .image-tile {{
                border: 1px solid #ddd;
                padding: 5px;
                background-color: white;
                box-shadow: 3px 3px 8px rgba(0,0,0,0.15);
                text-align: center;
                border-radius: 8px;
                transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
            }}
            .image-tile:hover {{
                transform: translateY(-5px);
                box-shadow: 5px 5px 15px rgba(0,0,0,0.2);
            }}
            .image-tile img {{
                width: 150px;
                height: 150px;
                object-fit: cover;
                display: block;
                margin: 0 auto;
                border-radius: 4px;
            }}
            .image-tile a {{
                text-decoration: none;
                color: #333;
                font-size: 0.9em;
                display: block;
                font-weight: bold;
            }}
            .image-tile a:hover {{
                color: #007bff;
            }}
            .image-filename {{
                font-size: 0.8em;
                color: #555;
                margin-top: 2px;
                display: block;
                font-weight: normal;
            }}
            .image-date {{
                font-size: 0.75em;
                color: #888;
                margin-top: 2px;
                display: block;
                font-weight: normal;
            }}
            .no-images {{
                text-align: center;
                color: #666;
                font-style: italic;
                margin-top: 50px;
            }}
            .pagination {{
                text-align: center;
                margin-top: 30px;
                margin-bottom: 30px;
            }}
            .pagination a, .pagination span {{
                display: inline-block;
                padding: 10px 15px;
                margin: 0 3px;
                border: 1px solid #007bff;
                border-radius: 5px;
                text-decoration: none;
                color: #007bff;
                background-color: #fff;
                transition: background-color 0.3s, color 0.3s;
            }}
            .pagination a:hover {{
                background-color: #007bff;
                color: #fff;
            }}
            .pagination span.current-page {{
                background-color: #007bff;
                color: #fff;
                font-weight: bold;
                border-color: #007bff;
            }}
            .pagination span.disabled {{
                border: 1px solid #ccc;
                color: #ccc;
                background-color: #f9f9f9;
                cursor: not-allowed;
            }}
            .subdirs {{
                text-align: center;
                margin-top: 30px;
                margin-bottom: 30px;
            }}
            .subdirs a {{
                display: inline-block;
                padding: 10px 15px;
                margin: 5px;
                border: 1px solid #28a745;
                border-radius: 5px;
                text-decoration: none;
                color: #28a745;
                background-color: #fff;
                transition: background-color 0.3s, color 0.3s;
            }}
            .subdirs a:hover {{
                background-color: #28a745;
                color: #fff;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <div class="gallery-container">
    """

    if not tiles:
        html_content += f"<p class='no-images'>{empty_message}</p>"
    else:
        for tile in tiles:
            href = tile.get("href", "#")
            img_src = tile.get("img_src", "")
            filename = tile.get("filename", "")
            caption = tile.get("caption", "")
            html_content += f"""
            <div class="image-tile">
                <a href="{href}" target="_blank">
                    <img src="{img_src}" alt="image">
                    <p class="image-filename">{filename}</p>
                    <p class="image-date">{caption}</p>
                </a>
            </div>
            """

    html_content += """
        </div>
        <div class="pagination">
    """

    # Previous
    dir_param = f"&dir={current_dir_rel}" if current_dir_rel else ""
    if page > 1:
        html_content += f"<a href='/?page={page - 1}{dir_param}'>&laquo; Previous</a>"
    else:
        html_content += "<span class='disabled'>&laquo; Previous</span>"

    # Numbered links
    if total_pages > 0:
        for p_num in range(start_page_num, end_page_num + 1):
            if p_num == page:
                html_content += f"<span class='current-page'>{p_num}</span>"
            else:
                html_content += f"<a href='/?page={p_num}{dir_param}'>{p_num}</a>"

    # Next
    if page < total_pages:
        html_content += f"<a href='/?page={page + 1}{dir_param}'>Next &raquo;</a>"
    else:
        html_content += "<span class='disabled'>Next &raquo;</span>"

    html_content += """
        </div>
    """

    # Subdirectories
    if subdirs:
        html_content += '<div class="subdirs"><h3>Subdirectories:</h3>'
        for display_name, rel_path in subdirs:
            html_content += f'<a href="/?dir={rel_path}">{display_name}</a>'
        html_content += '</div>'

    html_content += """
    </body>
    </html>
    """

    return render_template_string(html_content)
