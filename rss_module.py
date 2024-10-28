# rss_module.py
import feedparser
from rich.console import Console
from rich.table import Table

console = Console()

def fetch_rss_feed(url):
    console.print(f"Fetching RSS feed from [cyan]{url}[/cyan]")
    feed = feedparser.parse(url)

    if feed.bozo:
        console.print("[red]Failed to retrieve feed. Please check the URL.[/red]")
        return
    
    table = Table(title="RSS Feed Articles")
    table.add_column("Title", style="bold")
    table.add_column("Link", style="dim")

    for entry in feed.entries[:5]:  # Limit to 5 entries for readability
        table.add_row(entry.title, entry.link)

    console.print(table)
