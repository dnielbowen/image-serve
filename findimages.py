import os
import sys
import stat # Not strictly necessary for os.stat, but good practice if using stat constants

def create_image_symlinks():
    # Get the directory where the script itself is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define the subdirectory for symlinks
    images_subdir = os.path.join(script_dir, 'images')

    # Create the images subdirectory if it doesn't exist
    os.makedirs(images_subdir, exist_ok=True)

    # --- NEW: Get root directory from command line argument ---
    if len(sys.argv) < 2:
        print("Usage: python findimages.py <root_directory_to_search>")
        print("Example: python findimages.py /path/to/your/photos")
        sys.exit(1) # Exit with an error code

    root_search_dir = sys.argv[1]

    # Validate the provided root directory
    if not os.path.isdir(root_search_dir):
        print(f"Error: The specified root directory '{root_search_dir}' does not exist or is not a directory.")
        sys.exit(1) # Exit with an error code
    # --- END NEW ---

    # Define common image file extensions
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
    
    symlink_count = 0
    max_symlinks = 2000
    total_images_found = 0 # New counter for total images found

    print(f"Starting image symlink creation process...")
    print(f"Searching for images recursively in: '{root_search_dir}'") # Updated print statement

    # First pass: Count all image files
    for root, _, files in os.walk(root_search_dir): # Updated search directory
        for file in files:
            if file.lower().endswith(image_extensions):
                total_images_found += 1
    
    print(f"Total images found in '{root_search_dir}' and its subdirectories: {total_images_found}") # Updated print
    print(f"Creating symlinks in: '{images_subdir}'")
    print(f"Limiting to the first {max_symlinks} images found.")

    # Second pass: Create symlinks (limited by max_symlinks)
    # Reset walk to start from the beginning for symlink creation
    for root, _, files in os.walk(root_search_dir): # Updated search directory
        if symlink_count >= max_symlinks:
            break # Stop if we've reached the maximum number of symlinks

        for file in files:
            if symlink_count >= max_symlinks:
                break # Stop if we've reached the maximum within the current directory's files

            # Check if the file has an image extension (case-insensitive)
            if file.lower().endswith(image_extensions):
                source_path = os.path.join(root, file)
                symlink_name = os.path.basename(source_path) # Use original filename for the symlink
                destination_path = os.path.join(images_subdir, symlink_name) # Updated destination path

                # Check if a file or symlink with the same name already exists in the destination
                if os.path.exists(destination_path) or os.path.islink(destination_path):
                    print(f"Skipping '{source_path}': A file or symlink named '{symlink_name}' already exists in '{images_subdir}'.")
                    continue

                try:
                    # Create the symbolic link
                    os.symlink(source_path, destination_path)
                    print(f"Created symlink: '{symlink_name}' -> '{source_path}'")
                    symlink_count += 1

                    # Get original file's access and modification times
                    source_stat = os.stat(source_path)
                    atime = source_stat.st_atime # Access time
                    mtime = source_stat.st_mtime # Modification time

                    # Set the symlink's access and modification times to match the source
                    # Use follow_symlinks=False to ensure the symlink's own timestamps are modified,
                    # not the target file's timestamps.
                    os.utime(destination_path, (atime, mtime), follow_symlinks=False)
                    print(f"Set timestamps for '{symlink_name}' to match source.")

                except OSError as e:
                    # Catch OS-related errors (e.g., permissions, invalid path)
                    print(f"Error creating or setting timestamps for symlink for '{source_path}' to '{destination_path}': {e}")
                except Exception as e:
                    # Catch any other unexpected errors
                    print(f"An unexpected error occurred for '{source_path}': {e}")

    print(f"\nProcess finished. Successfully created {symlink_count} symlinks.")
    if symlink_count < max_symlinks:
        print(f"Fewer than {max_symlinks} images were found or could be linked.")

if __name__ == '__main__':
    create_image_symlinks()
