# Apple Notes to Notion via Dify

Automate migration of Apple Notes to Notion using a hybrid local + Dify workflow.

https://cloud.dify.ai/app/6a97c493-eabc-44c0-ab1d-06f5d854fa62/workflow

**Features:**
- Preserves original note creation dates (from macOS metadata)
- Uploads images/attachments to Dropbox for embedding in Notion
- AI-powered categorization using LLM (DeepSeek via Dify)
- Handles 267+ notes with rate-limited Notion API integration

---

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd apple_notes_proj

# Install dependencies
pip install dropbox
```

### 2. Configure Credentials

#### Dropbox Setup
1. Go to https://www.dropbox.com/developers/apps
2. Create app → "Scoped access" → "App folder"
3. Generate access token
4. Copy `upload_to_dropbox.py.example` to `upload_to_dropbox.py`:
   ```bash
   cp upload_to_dropbox.py.example upload_to_dropbox.py
   ```
5. Replace `YOUR_DROPBOX_ACCESS_TOKEN_HERE` with your actual token

#### Google Credentials (if using Google Drive integration)
1. Copy `credentials.json.example` to `credentials.json`:
   ```bash
   cp credentials.json.example credentials.json
   ```
2. Fill in your Google OAuth credentials

### 3. Export Apple Notes

Export your Apple Notes to Markdown format using a tool like **Exporter** (Mac App Store).

Expected folder structure:
```
apple_notes/
├── [Note Title 1].md
├── [Note Title 2].md
├── images/              # Image attachments
│   ├── UUID1.png
│   └── UUID2.heic
└── attachments/         # File attachments
    ├── UUID3.pdf
    └── UUID4.m4a
```

### 4. Upload Attachments to Dropbox

```bash
python3 upload_to_dropbox.py
```

This creates:
- Dropbox folder `/Apple Notes Attachments`
- `attachment_mapping.json` (local file mapping UUIDs to Dropbox share links)

### 5. Generate Dify Input

```bash
python3 prepare_json.py
```

This creates:
- `dify_input.json` - Full dataset (267 notes)
- `input_test_to_dify.json` - Test subset (5 notes with attachments)

### 6. Run Dify Workflow

1. Upload `input_test_to_dify.json` to Dify for testing
2. After validation, upload `dify_input.json` for full import

See [AI_summary.md](AI_summary.md) for detailed Dify workflow configuration.

---

## Project Structure

```
.
├── apple_notes/                    # Your exported notes (gitignored)
│   ├── *.md
│   ├── images/
│   └── attachments/
│
├── upload_to_dropbox.py            # Your local copy (gitignored)
├── upload_to_dropbox.py.example    # Template
├── credentials.json                # Your local copy (gitignored)
├── credentials.json.example        # Template
├── attachment_mapping.json         # Generated (gitignored)
├── dify_input.json                 # Generated (gitignored)
├── input_test_to_dify.json         # Generated (gitignored)
│
├── prepare_json.py                 # Shared script
├── AI_summary.md                   # Detailed documentation
└── .gitignore                      # Excludes personal data
```

---

## Security Notes

**Never commit these files:**
- `upload_to_dropbox.py` (contains access token)
- `credentials.json` (contains OAuth secrets)
- `token.pickle` (cached auth token)
- `apple_notes/` (personal note content)
- `attachment_mapping.json` (Dropbox links to your files)
- `dify_input.json` (all your note content)

The `.gitignore` is pre-configured to exclude all sensitive and personal files.

---

## Dify Workflow Requirements

### Environment Variables
- `NOTION_TOKEN` - Notion integration token
- `NOTION_DATABASE_ID` - Target database ID

### LLM Configuration
- Model: DeepSeek-V3.2 (via Siliconflow)
- Batch categorization of all notes
- Structured JSON output

See [AI_summary.md](AI_summary.md) for complete workflow documentation.

---

## License

MIT
