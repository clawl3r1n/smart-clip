import click
import pyperclip
import time
import sqlite3
import re
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table

# Try importing pygetwindow for context capture
try:
    import pygetwindow as gw
    HAS_WINDOW_API = True
except ImportError:
    HAS_WINDOW_API = False

console = Console()

# --- Database Setup ---
DB_NAME = "clipboard.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clips
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  content TEXT UNIQUE, 
                  category TEXT, 
                  source_app TEXT,
                  window_title TEXT,
                  timestamp DATETIME)''')
    conn.commit()
    conn.close()

# --- Helpers ---
def get_active_window_info():
    if not HAS_WINDOW_API:
        return "Unknown", "Unknown"
    try:
        window = gw.getActiveWindow()
        if window:
            return "App", window.title # Limitation: pygetwindow doesn't easily give process name cross-platform
        return "Unknown", "Unknown"
    except:
        return "Unknown", "Unknown"

def categorize(text):
    text = text.strip()
    if re.match(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text): return "Link"
    if re.match(r'[\w\.-]+@[\w\.-]+\.\w+', text): return "Email"
    if re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', text): return "Color"
    if re.match(r'^\+?[\d\s-]{10,}$', text): return "Phone"
    if any(char in text for char in ['{', '}', ';', 'def ', 'class ', 'import ']) and len(text) > 20: return "Code"
    return "Text"

def format_clip(content, source, title, timestamp, fmt):
    dt = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")
    
    if fmt == 'markdown':
        return f"> {content}\n\n— *Copied from [{title}] at {dt}*"
    elif fmt == 'citation':
        return f'"{content}" ({title}, {dt})'
    elif fmt == 'json':
        return json.dumps({
            "content": content,
            "source": source,
            "title": title,
            "timestamp": timestamp
        }, indent=2)
    else:
        return content

# --- CLI Commands ---

@click.group()
def cli():
    """Smart Clip - Organize your clipboard history."""
    init_db()

@cli.command()
def watch():
    """Start watching the clipboard for changes."""
    console.print("[green]Listening for clipboard changes... Press Ctrl+C to stop.[/green]")
    last_clip = ""
    
    try:
        while True:
            current_clip = pyperclip.paste()
            if current_clip != last_clip and current_clip.strip():
                last_clip = current_clip
                category = categorize(current_clip)
                timestamp = datetime.now().isoformat()
                source_app, window_title = get_active_window_info()
                
                # Save to DB
                try:
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    c.execute("""INSERT OR REPLACE INTO clips 
                                 (content, category, source_app, window_title, timestamp) 
                                 VALUES (?, ?, ?, ?, ?)""",
                              (current_clip, category, source_app, window_title, timestamp))
                    conn.commit()
                    conn.close()
                    console.print(f"[bold blue]Saved:[/bold blue] ({category}) from [dim]{window_title}[/dim]")
                except Exception as e:
                    console.print(f"[red]Error saving clip:[/red] {e}")
            
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped listening.[/yellow]")

@cli.command()
@click.option('--category', '-c', help='Filter by category')
@click.option('--limit', '-l', default=10, help='Number of clips to show')
def list(category, limit):
    """List recent clipboard history."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    query = "SELECT category, content, window_title, timestamp FROM clips"
    params = []
    
    if category:
        query += " WHERE category = ?"
        params.append(category)
        
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    c.execute(query, tuple(params))
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        console.print("[yellow]No clips found.[/yellow]")
        return

    table = Table(title="Clipboard History")
    table.add_column("Time", style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Source", style="magenta")
    table.add_column("Content", style="white")

    for cat, content, title, ts in rows:
        dt = datetime.fromisoformat(ts)
        time_str = dt.strftime("%H:%M")
        display_content = (content[:40] + '...') if len(content) > 40 else content
        table.add_row(time_str, cat, title or "Unknown", display_content)

    console.print(table)

@cli.command()
@click.option('--format', '-f', default='raw', type=click.Choice(['raw', 'markdown', 'citation', 'json']), help='Output format')
def paste(format):
    """Output the last clip in a specific format."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT content, source_app, window_title, timestamp FROM clips ORDER BY timestamp DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    
    if row:
        output = format_clip(row[0], row[1], row[2], row[3], format)
        click.echo(output)
        # Optional: copy back to clipboard
        pyperclip.copy(output)
    else:
        console.print("[red]Clipboard history is empty.[/red]")

if __name__ == '__main__':
    cli()
