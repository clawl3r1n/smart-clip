import click
import pyperclip
import time
import sqlite3
import re
from datetime import datetime
from rich.console import Console
from rich.table import Table

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
                  timestamp DATETIME)''')
    conn.commit()
    conn.close()

# --- Categorization Logic ---
def categorize(text):
    text = text.strip()
    
    # 1. URL
    if re.match(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text):
        return "Link"
    
    # 2. Email
    if re.match(r'[\w\.-]+@[\w\.-]+\.\w+', text):
        return "Email"
    
    # 3. Hex Color
    if re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', text):
        return "Color"
    
    # 4. Phone (Simple)
    if re.match(r'^\+?[\d\s-]{10,}$', text):
        return "Phone"
    
    # 5. Code (Naive check for programming syntax)
    if any(char in text for char in ['{', '}', ';', 'def ', 'class ', 'import ']) and len(text) > 20:
        return "Code"
        
    return "Text"

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
                
                # Save to DB
                try:
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    # Store unique clips only (replace timestamp if duplicate)
                    c.execute("INSERT OR REPLACE INTO clips (content, category, timestamp) VALUES (?, ?, ?)",
                              (current_clip, category, timestamp))
                    conn.commit()
                    conn.close()
                    console.print(f"[bold blue]Saved:[/bold blue] ({category}) {current_clip[:50]}...")
                except Exception as e:
                    console.print(f"[red]Error saving clip:[/red] {e}")
            
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped listening.[/yellow]")

@cli.command()
@click.option('--category', '-c', help='Filter by category (Link, Email, Code, etc.)')
@click.option('--limit', '-l', default=10, help='Number of clips to show')
def list(category, limit):
    """List recent clipboard history."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    query = "SELECT category, content, timestamp FROM clips"
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
    table.add_column("Content", style="white")

    for cat, content, ts in rows:
        # Format timestamp
        dt = datetime.fromisoformat(ts)
        time_str = dt.strftime("%Y-%m-%d %H:%M")
        # Truncate content for display
        display_content = (content[:60] + '...') if len(content) > 60 else content
        table.add_row(time_str, cat, display_content)

    console.print(table)

@cli.command()
@click.argument('query')
def search(query):
    """Search for specific text in your clips."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT category, content, timestamp FROM clips WHERE content LIKE ? ORDER BY timestamp DESC", 
              ('%' + query + '%',))
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        console.print(f"[yellow]No matches found for '{query}'.[/yellow]")
        return

    table = Table(title=f"Search Results: '{query}'")
    table.add_column("Type", style="cyan")
    table.add_column("Content", style="white")

    for cat, content, ts in rows:
        table.add_row(cat, content)

    console.print(table)

@cli.command()
def clear():
    """Clear all history."""
    if click.confirm('Are you sure you want to delete all clipboard history?'):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM clips")
        conn.commit()
        conn.close()
        console.print("[green]History cleared.[/green]")

if __name__ == '__main__':
    cli()
