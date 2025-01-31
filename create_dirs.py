import os

# Create upload directories
upload_dirs = [
    'app/static/uploads',
    'app/static/uploads/attachments'
]

for dir_path in upload_dirs:
    os.makedirs(dir_path, exist_ok=True)
    print(f"Created directory: {dir_path}")
