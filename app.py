import os
from flask import Flask, render_template_string, send_from_directory, abort, request
from datetime import datetime # Import datetime for date formatting

app = Flask(__name__)

# Define common image file extensions (same as in copy.py)
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')

# Get the directory where app.py is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Now, define the directory where images (symlinks) are expected to be
IMAGES_DIR = os.path.join(SCRIPT_DIR, 'images')

# Pagination setting
IMAGES_PER_PAGE = 300
PAGINATION_LINKS_TO_SHOW = 10 # Number of numbered page links to display

@app.route('/')
def index():
    image_data_raw = [] # Will temporarily store (modification_time, filename, formatted_date_string) tuples
    
    # Ensure the images directory exists before trying to list its contents
    if not os.path.isdir(IMAGES_DIR):
        print(f"Warning: Image directory '{IMAGES_DIR}' not found.")
        # If the directory doesn't exist, no images can be found
        all_display_images = []
    else:
        # List files in the images subdirectory
        for filename in os.listdir(IMAGES_DIR):
            file_path = os.path.join(IMAGES_DIR, filename)
            # Check if the file has an image extension (case-insensitive)
            # and ensure it's a file (not a directory)
            if os.path.isfile(file_path) and filename.lower().endswith(IMAGE_EXTENSIONS):
                try:
                    # Get the modification time of the file
                    mtime = os.path.getmtime(file_path)
                    # Format the modification time to "Mon Day, Year" (e.g., Aug 23, 2022)
                    dt_object = datetime.fromtimestamp(mtime)
                    formatted_date = dt_object.strftime("%b %d, %Y")
                    image_data_raw.append((mtime, filename, formatted_date))
                except OSError as e:
                    print(f"Warning: Could not get modification time for '{filename}': {e}")
                    # If mtime can't be retrieved, still include the file but with a placeholder date
                    image_data_raw.append((float('inf'), filename, "Date N/A")) # Put at the end if mtime fails
        
        # Sort images by modification time (earliest first)
        image_data_raw.sort()

        # Extract just the (filename, formatted_date) pairs in the sorted order for display
        all_display_images = [(filename, formatted_date) for mtime, filename, formatted_date in image_data_raw]

    # Pagination logic
    page = request.args.get('page', 1, type=int)
    total_images = len(all_display_images)
    total_pages = (total_images + IMAGES_PER_PAGE - 1) // IMAGES_PER_PAGE
    
    # Ensure page is within valid range
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    elif total_pages == 0: # Handle case with no images
        page = 1

    start_index = (page - 1) * IMAGES_PER_PAGE
    end_index = start_index + IMAGES_PER_PAGE
    
    current_page_images_for_display = all_display_images[start_index:end_index]

    # Calculate range for numbered pagination links
    # Determine the half-width of the pagination links to show around the current page
    half_links = PAGINATION_LINKS_TO_SHOW // 2
    
    start_page_num = max(1, page - half_links)
    end_page_num = min(total_pages, page + (PAGINATION_LINKS_TO_SHOW - 1 - half_links))

    # Adjust start_page_num if we hit the end of total_pages
    if end_page_num == total_pages:
        start_page_num = max(1, total_pages - PAGINATION_LINKS_TO_SHOW + 1)
    
    # Adjust end_page_num if we hit the beginning of total_pages (after potential end adjustment)
    if start_page_num == 1:
        end_page_num = min(total_pages, PAGINATION_LINKS_TO_SHOW)

    # Ensure start_page_num doesn't exceed end_page_num if total_pages is very small
    if total_pages == 0:
        start_page_num = 0
        end_page_num = 0
    elif start_page_num > end_page_num: # This can happen if total_pages < PAGINATION_LINKS_TO_SHOW
        start_page_num = 1
        end_page_num = total_pages


    # Generate HTML for the tiled view
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Image Gallery (Page {page} of {total_pages})</title>
        <style>
            body {{
                font-family: sans-serif;
                margin: 20px;
                background-color: #f0f0f0;
            }}
            h1 {{
                text-align: center;
                color: #333;
            }}
            .gallery-container {{
                display: flex;
                flex-wrap: wrap;
                gap: 4px; /* Reduced space between images */
                justify-content: center; /* Center the tiles */
                padding: 20px;
            }}
            .image-tile {{
                border: 1px solid #ddd;
                padding: 5px; /* Slightly reduced padding */
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
                width: 120px; /* Fixed width */
                height: 120px; /* Fixed height to ensure consistent tile size */
                object-fit: cover; /* Crop image to fit without distortion */
                display: block; /* Remove extra space below image */
                margin: 0 auto; /* Center image within its tile */
                border-radius: 4px;
            }}
            .image-tile a {{
                text-decoration: none;
                color: #333;
                font-size: 0.9em;
                display: block; /* Make the whole tile clickable */
                font-weight: bold;
            }}
            .image-tile a:hover {{
                color: #007bff;
            }}
            .image-date {{ /* New style for the date */
                font-size: 0.75em; /* Smaller font size */
                color: #888; /* Faint color */
                margin-top: 5px; /* Small margin above the date */
                display: block; /* Ensure it takes its own line */
                font-weight: normal; /* Override bold from parent 'a' tag */
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
                padding: 10px 15px; /* Slightly reduced padding for numbered links */
                margin: 0 3px; /* Reduced margin for numbered links */
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
        <h1>Local Image Gallery</h1>
        <div class="gallery-container">
    """

    if not current_page_images_for_display:
        html_content += "<p class='no-images'>No image files found in the 'images' directory or on this page.</p>"
    else:
        for img_file, img_date in current_page_images_for_display: # Unpack filename and date
            # Link to the raw image, open in new tab
            # Image source points to the /images/ route
            html_content += f"""
            <div class="image-tile">
                <a href="/images/{img_file}" target="_blank">
                    <img src="/images/{img_file}" alt="{img_file}">
                    <p class="image-date">{img_date}</p> <!-- Added date here -->
                </a>
            </div>
            """

    html_content += """
        </div>
        <div class="pagination">
    """
    
    # Previous page link
    if page > 1:
        html_content += f"<a href='/?page={page - 1}'>&laquo; Previous</a>"
    else:
        html_content += "<span class='disabled'>&laquo; Previous</span>"

    # Numbered page links
    if total_pages > 0: # Only show numbered links if there are pages
        for p_num in range(start_page_num, end_page_num + 1):
            if p_num == page:
                html_content += f"<span class='current-page'>{p_num}</span>"
            else:
                html_content += f"<a href='/?page={p_num}'>{p_num}</a>"

    # Next page link
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

@app.route('/images/<filename>')
def serve_image(filename):
    # Serve the image file from the IMAGES_DIR
    # Flask's send_from_directory handles path safety.
    try:
        return send_from_directory(IMAGES_DIR, filename)
    except FileNotFoundError:
        # If the file doesn't exist, return a 404 error
        abort(404)

if __name__ == '__main__':
    # Run the Flask app
    # debug=True allows auto-reloading on code changes and provides more detailed error messages.
    # In a production environment, you would use a WSGI server like Gunicorn or uWSGI.
    app.run(debug=True)
