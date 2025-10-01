import os
import sys
import json
from datetime import datetime

def generate_image_index():
    """
    Traverses a specified root directory, finds image files, and generates
    a JSON index containing their absolute paths and modification timestamps.
    """
    if len(sys.argv) < 3:
        print("Usage: python generate_index.py <root_directory_to_search> <output_json_file>")
        print("Example: python generate_index.py /path/to/your/photos image_index.json")
        sys.exit(1)

    root_search_dir = sys.argv[1]
    output_json_path = sys.argv[2]

    if not os.path.isdir(root_search_dir):
        print(f"Error: The specified root directory '{root_search_dir}' does not exist or is not a directory.")
        sys.exit(1)

    # Define common image file extensions
    image_extensions = ('.png', '.jpg', '.jpeg', '.heif', '.gif', '.bmp', 
                        '.tiff', '.webp')
    
    image_index_data = []
    processed_count = 0

    print(f"Starting image index generation...")
    print(f"Searching for images recursively in: '{root_search_dir}'")
    print(f"Output will be saved to: '{output_json_path}'")

    for root, _, files in os.walk(root_search_dir):
        for file in files:
            full_file_path = os.path.join(root, file)

            # Skip AppleDouble files (._ files)
            if file.startswith('._'):
                # print(f"Skipping metadata file: '{full_file_path}'") # Uncomment for debugging
                continue
            
            # Check if the file has an image extension (case-insensitive)
            if not file.lower().endswith(image_extensions):
                # print(f"Skipping non-image file: '{full_file_path}'") # Uncomment for debugging
                continue

            # If we reach here, it's an image file and not a metadata file
            try:
                # Get absolute path to ensure it's fully qualified
                absolute_path = os.path.abspath(full_file_path)
                mtime = os.path.getmtime(absolute_path)
                
                image_index_data.append({
                    "path": absolute_path,
                    "mtime": mtime
                })
                processed_count += 1
                if processed_count % 1000 == 0:
                    print(f"Indexed {processed_count} images so far...")

            except OSError as e:
                print(f"Warning: Could not access '{full_file_path}' (skipping): {e}")
            except Exception as e:
                print(f"Warning: An unexpected error occurred for '{full_file_path}' (skipping): {e}")

    # Sort the collected data by modification time (earliest first)
    image_index_data.sort(key=lambda x: x['mtime'])

    try:
        with open(output_json_path, 'w') as f:
            json.dump(image_index_data, f, indent=4)
        print(f"\nProcess finished. Successfully indexed {len(image_index_data)} images.")
        print(f"Index saved to '{output_json_path}'.")
    except IOError as e:
        print(f"Error: Could not write index to '{output_json_path}': {e}")
        sys.exit(1)

if __name__ == '__main__':
    generate_image_index()
