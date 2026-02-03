# Apple Notes to Notion via Dify - Project Summary

## Project Overview

This project automates the migration of Apple Notes to a Notion database using a hybrid approach:
- **Local preprocessing** (Python scripts) handles attachments, date extraction, and JSON preparation
- **Dify workflow** handles AI categorization and Notion API integration

**Current Scale**: 267 notes, 60 images, 11 attachments (PDFs, audio files)
**Estimated Runtime**: 20-40 minutes for full import (sequential processing to respect Notion API rate limits ~3 req/sec)

---

## Project Structure

```
apple_notes_proj/
│
├── apple_notes/                    # Exported Apple Notes (Markdown files)
│   ├── [note_title].md            # 267 Markdown note files
│   ├── images/                    # 60 image attachments (PNG, JPG, HEIC)
│   └── attachments/               # 11 file attachments (PDF, M4A audio)
│
├── upload_to_dropbox.py           # Step 1: Upload attachments to Dropbox
├── prepare_json.py                # Step 2: Generate JSON for Dify
├── attachment_mapping.json        # Maps local files to Dropbox share links
├── dify_input.json                # Final JSON input for Dify workflow
├── input_test_to_dify.json        # Test subset (5 notes with attachments)
│
├── credentials.json               # Dropbox API credentials
└── token.pickle                   # Dropbox auth token cache
```

---

## Pre-Dify Preparation Steps

### Step 1: Export Apple Notes

Export your Apple Notes to Markdown format using a tool like:
- **Exporter** (Mac App Store)
- **Notes Exporter**
- Any tool that exports to Markdown with `images/` and `attachments/` subfolders

**Expected output structure:**
```
apple_notes/
├── [Note Title 1].md
├── [Note Title 2].md
├── images/
│   ├── UUID1.png
│   └── UUID2.heic
└── attachments/
    ├── UUID3.pdf
    └── UUID4.m4a
```

### Step 2: Configure Dropbox Upload

Edit `upload_to_dropbox.py`:

1. **Get Dropbox Access Token**:
   - Go to https://www.dropbox.com/developers/apps
   - Create new app → "Scoped access" → "App folder"
   - Generate access token (valid for 4 hours, or refresh token for production)

2. **Update the ACCESS_TOKEN** (line 6):
   ```python
   ACCESS_TOKEN = 'your-token-here'
   ```

3. **Run the upload script**:
   ```bash
   python3 upload_to_dropbox.py
   ```

**What it does:**
- Creates `/Apple Notes Attachments` folder in Dropbox
- Uploads all images and attachments
- Generates shareable links
- Saves mapping to `attachment_mapping.json`

**Output verification:**
- Check `attachment_mapping.json` contains entries like:
  ```json
  {"images/UUID.png": "https://www.dropbox.com/scl/fi/...", ...}
  ```

### Step 3: Generate Dify Input JSON

**Run the preparation script**:
```bash
python3 prepare_json.py
```

**What it does:**
- Reads all `.md` files from `apple_notes/`
- Extracts original creation date from macOS metadata (`kMDItemContentCreationDate`)
- Replaces local image/attachment references with Dropbox share links
- Generates `dify_input.json` with format:
  ```json
  {
    "notes": [
      {
        "filename": "Note Title.md",
        "content_with_links": "# Note Title\n\nContent with ![image](dropbox-link)...",
        "date": "2024-06-01"
      }
    ]
  }
  ```

**Verification output:**
```
JSON created: dify_input.json with 267 notes
Total dropbox links in output: 71
Notes with dropbox links: 25
```

### Step 4: Create Test File (Optional but Recommended)

Create a smaller test file for Dify workflow validation:

```bash
python3 -c "
import json
with open('dify_input.json', 'r') as f:
    data = json.load(f)
notes = [n for n in data['notes'] if 'dropbox.com' in n['content_with_links']][:5]
with open('input_test_to_dify.json', 'w') as f:
    json.dump({'notes': notes}, f, ensure_ascii=False, indent=2)
print(f'Test file created with {len(notes)} notes')
"
```

---

## Dify Workflow Configuration

### Environment Variables (Required)

In Dify Settings → Environment Variables, add:

| Variable | Description | Example |
|----------|-------------|---------|
| `NOTION_TOKEN` | Notion Integration Token | `secret_xxx...` |
| `NOTION_DATABASE_ID` | Target database ID | `1234567890abcdef...` |

**Get Notion credentials:**
1. Go to https://www.notion.so/my-integrations
2. Create new integration → Copy "Internal Integration Token"
3. Create/connect database → Share with integration → Copy database ID from URL

### LLM Configuration

- **Model**: DeepSeek-V3.2 (via Siliconflow)
- **Purpose**: Generate 8 global categories and assign to each note
- **Output Format**: Structured JSON with `categories` field

### Workflow Nodes Overview

```
Start → Doc Extractor → Code (Parse JSON) → LLM (Categorize) → Iteration → Output
                                          │
                                          └─→ Iteration sub-flow:
                                              Start → Code (Extract vars) → Code (Format Notion payload) → HTTP (Create page) → End
```

**Node Details:**

| Node | Type | Purpose |
|------|------|---------|
| Start | Input | Accept JSON file upload |
| Doc Extractor | Document | Extract text from uploaded JSON |
| Code: From Str to Array | Code (Python) | Parse JSON string to notes list |
| LLM 2 | LLM | Batch categorize all notes, add `categories` field |
| Iteration | Iteration | Loop over each note in updated array |
| → Code: Extract Variables | Code | Extract title, date, categories, content |
| → Code: Format Data | Code | Build Notion API payload, parse MD to blocks (max 100) |
| → HTTP: Create Pages | HTTP Request | POST to Notion API `/v1/pages` with 3x retry |
| End | End | Return array of HTTP status codes |

---

## Notion Database Schema

The Dify workflow expects a database with these properties:

| Property | Type | Populated By |
|----------|------|--------------|
| Name | Title | Note filename (cleaned) |
| Date | Date | Extracted from macOS metadata |
| Categories | Multi-select | AI-generated by LLM |
| Content | Rich Text | Full note content with Dropbox links |

**Block Limitations:**
- Maximum 100 blocks per page (enforced in "Format Data" code node)
- Images render as embeds using Dropbox links
- PDFs render as hyperlinks

---

## Execution Guide

### Option A: Test Run (Recommended First)

1. Upload `input_test_to_dify.json` to Dify workflow
2. Run workflow
3. Verify 5 notes created in Notion with correct:
   - Titles
   - Dates
   - Categories (AI-generated)
   - Image/file links render correctly

### Option B: Full Import

1. Upload `dify_input.json` to Dify workflow
2. Run workflow
3. Monitor for ~20-40 minutes (267 notes sequential)
4. Check output array for any failed requests (non-200 status codes)

---

## Troubleshooting

### Issue: No Dropbox links in output

**Cause**: `attachment_mapping.json` missing or empty
**Fix**: Re-run `upload_to_dropbox.py`

### Issue: Wrong dates (all same date)

**Cause**: Using file system dates instead of note creation dates
**Fix**: `prepare_json.py` now uses `mdls` to read macOS metadata. Ensure running on macOS with exported notes intact.

### Issue: Notion API rate limiting

**Symptom**: 429 errors in output
**Solution**: Workflow already uses sequential iteration (non-parallel). If still rate-limited, add delay in HTTP node or reduce batch size.

### Issue: Links not rendering in Notion

**Cause**: Dropbox links need `?dl=0` parameter for embeds
**Fix**: Ensure `upload_to_dropbox.py` generated proper share links with `sharing_create_shared_link_with_settings()`

---

## File Dependencies

```
prepare_json.py
├── requires: attachment_mapping.json (from upload_to_dropbox.py)
├── requires: apple_notes/*.md
├── requires: apple_notes/images/*
├── requires: apple_notes/attachments/*
└── outputs: dify_input.json

upload_to_dropbox.py
├── requires: credentials.json
├── requires: apple_notes/images/*
├── requires: apple_notes/attachments/*
└── outputs: attachment_mapping.json
```

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Total Notes | 267 |
| Notes with Attachments | ~25 (9%) |
| Total Attachments | 71 (60 images + 11 files) |
| JSON Size | ~250 KB |
| Estimated Processing Time | 20-40 minutes |
| Notion API Calls | 267 (1 per note) |

---

## Architecture Decisions

1. **Dropbox for Media**: Bypasses Dify's file size limits and enables reliable embedding in Notion
2. **Local Date Extraction**: macOS metadata preserves original note creation dates
3. **Batch Categorization**: Single LLM call categorizes all notes at once (more consistent global categories)
4. **Sequential Iteration**: Respects Notion API rate limits (~3 req/sec)
5. **Markdown to Blocks**: Custom Code node converts MD headings/lists/links to Notion block format
