# Smart Clip 📎

A context-aware clipboard manager that captures **where** and **when** you copied something.

## Features
- **Context Capture**: Records the application name, window title, and timestamp.
- **Smart Formatting**: Retrieve clips formatted as citations or Markdown blocks.
- **Auto-Categorization**: Detects URLs, Emails, Phone Numbers, Code Snippets, etc.
- **Searchable History**: Retrieve past clips by type, content, or source app.

## Installation

```bash
git clone https://github.com/clawl3r1n/smart-clip.git
cd smart-clip
pip install -r requirements.txt
```

## Usage

### 1. Watch Mode (Enhanced)
Starts the listener. It now attempts to detect the active window title (works best on Windows/Linux with `pygetwindow`).
```bash
python main.py watch
```

### 2. Formatted Paste
Get the last clip formatted with its context:
```bash
python main.py paste --format markdown
```
**Output:**
```markdown
> "The text you copied..."
— Copied from [Chrome: Stack Overflow] at 2023-10-27 14:00
```

### 3. List History
Show source applications:
```bash
python main.py list
```

## Formats Supported
- `raw`: Just the text (default).
- `markdown`: Blockquote with source metadata.
- `json`: Full metadata object.
- `citation`: "Text" (Source, Date).
