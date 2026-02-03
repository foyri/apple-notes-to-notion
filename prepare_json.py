import os
import json
import re
import datetime
import subprocess

base_dir = 'apple_notes'

def get_note_creation_date(md_path):
    """Get the original note creation date from macOS metadata."""
    try:
        result = subprocess.run(
            ['mdls', '-raw', '-name', 'kMDItemContentCreationDate', md_path],
            capture_output=True,
            text=True,
            check=True
        )
        date_str = result.stdout.strip()
        # Parse format: 2024-06-01 07:16:46 +0000
        if date_str and date_str != '(null)':
            dt = datetime.datetime.strptime(date_str.split(' +')[0], '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%Y-%m-%d')
    except Exception:
        pass
    # Fallback to file system creation time
    ctime = os.path.getctime(md_path)
    return datetime.datetime.fromtimestamp(ctime).strftime('%Y-%m-%d')
with open('attachment_mapping.json', 'r') as f:
    mapping = json.load(f)

md_files = [f for f in os.listdir(base_dir) if f.endswith('.md')]
notes = []

# Image extensions that should use ![alt](url) format
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.heic', '.gif', '.webp', '.bmp'}

def find_dropbox_link(folder, filename):
    """Find dropbox link, trying both images/ and attachments/ prefixes."""
    # Try the path as specified first
    ref = f"{folder}{filename}"
    if ref in mapping:
        return mapping[ref]

    # If not found and folder is attachments/, try images/
    if folder == 'attachments/':
        ref = f"images/{filename}"
        if ref in mapping:
            return mapping[ref]

    # If not found and folder is images/, try attachments/
    if folder == 'images/':
        ref = f"attachments/{filename}"
        if ref in mapping:
            return mapping[ref]

    return None

for md in md_files:
    md_path = os.path.join(base_dir, md)
    with open(md_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Replace markdown links with Dropbox links
    # Pattern matches: [alt_text](images/filename.ext) or [alt_text](attachments/filename.ext)
    def replace_link(match):
        alt_text = match.group(1)
        folder = match.group(2)  # "images/" or "attachments/"
        filename = match.group(3)

        link = find_dropbox_link(folder, filename)

        if link:
            # Check if it's an image based on extension
            ext = os.path.splitext(filename)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                return f"![{alt_text}]({link})"
            else:
                return f"[{alt_text}]({link})"
        # Return original if no mapping found
        return match.group(0)

    # Match pattern: [alt_text](images/filename) or [alt_text](attachments/filename)
    # The alt_text can be empty or contain any characters except ]
    # The filename can contain: letters, numbers, hyphens, underscores, and dots
    content_with_links = re.sub(
        r'\[([^\]]*)\]\((images/|attachments/)([A-Za-z0-9_-]+\.[A-Za-z0-9]+)\)',
        replace_link,
        content
    )

    # Extract date from macOS file metadata (original note creation date)
    date = get_note_creation_date(md_path)

    notes.append({
        'filename': md,
        'content_with_links': content_with_links,
        'date': date
    })

# Save JSON
output_file = 'dify_input.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({'notes': notes}, f, ensure_ascii=False, indent=2)

print(f"JSON created: {output_file} with {len(notes)} notes")

# Verification: count how many dropbox links are in the output
with open(output_file, 'r', encoding='utf-8') as f:
    content = f.read()
    dropbox_count = content.count('dropbox.com')
    print(f"Total dropbox links in output: {dropbox_count}")

# Detailed verification
with open(output_file, 'r', encoding='utf-8') as f:
    data = json.load(f)
    notes_with_links = sum(1 for note in data['notes'] if 'dropbox.com' in note['content_with_links'])
    print(f"Notes with dropbox links: {notes_with_links}")
