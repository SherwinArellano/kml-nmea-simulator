import os
import shutil

src_dir = "samples"
dst_dir = "maps"

# Create destination folder if it doesn't exist
os.makedirs(dst_dir, exist_ok=True)

for fname in os.listdir(src_dir):
    src_path = os.path.join(src_dir, fname)
    dst_path = os.path.join(dst_dir, fname)

    # Only proceed if it's a file (e.g., a .kml)
    if os.path.isfile(src_path):
        # Copy and overwrite if exists
        shutil.copy2(src_path, dst_path)
