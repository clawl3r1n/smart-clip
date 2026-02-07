# Smart Clip 📎

A smart clipboard manager that automatically categorizes your copied text using regex patterns and stores it in a searchable local database.

## Features
- **Auto-Categorization**: Detects URLs, Emails, Phone Numbers, Code Snippets, Hex Colors, and more.
- **Searchable History**: Retrieve past clips by type, content, or date.
- **CLI Interface**: Simple command-line tools to view and manage your clipboard history.
- **Background Daemon**: Runs silently in the background capturing everything you copy.

## Installation

```bash
git clone https://github.com/clawl3r1n/smart-clip.git
cd smart-clip
pip install -r requirements.txt
```

## Usage

### 1. Start the Background Listener
This will monitor your clipboard for changes.
```bash
python main.py watch
```

### 2. View History
Show all recent clips:
```bash
python main.py list
```

Filter by category (e.g., only show links):
```bash
python main.py list --category Link
```

Search content:
```bash
python main.py search "project"
```

## Categories
The tool currently recognizes:
- `Link` (http/https URLs)
- `Email`
- `Color` (Hex codes like #FF0000)
- `Phone` (Simple phone number patterns)
- `Code` (Blocks with typical programming syntax like `{ } ;`)
- `Text` (Everything else)

## Data Storage
Clips are stored locally in `clipboard.db` (SQLite).
