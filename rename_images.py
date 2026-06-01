import os
import glob

# Directory containing the images
image_dir = r"c:\Users\zufarkhon\Desktop\bot\imagebook"

# Get all PNG files
png_files = glob.glob(os.path.join(image_dir, "*.png"))

# Sort files by creation time
png_files.sort(key=os.path.getctime)

# Rename files starting from page_5.png (since page_1-4 already exist)
start_page = 5
for i, file_path in enumerate(png_files):
    page_num = start_page + i
    new_name = f"page_{page_num}.png"
    new_path = os.path.join(image_dir, new_name)
    
    # Skip if file already has correct name
    if os.path.basename(file_path) == new_name:
        continue
    
    try:
        os.rename(file_path, new_path)
        print(f"Renamed: {os.path.basename(file_path)} -> {new_name}")
    except Exception as e:
        print(f"Error renaming {file_path}: {e}")

print(f"\nDone! Renamed {len(png_files)} files starting from page_{start_page}.png")