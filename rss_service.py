import feedparser
from rich.console import Console

class RSSService:
    def __init__(self):
        self.console = Console()

    def display_feed(self, url):
        self.console.print(f"[blue]Fetching RSS feed from: {url}[/blue]")
        feed = feedparser.parse(url)

        for entry in feed.entries[:5]:  # Display the first 5 entries
            self.console.print(f"[bold green]Title:[/bold green] {entry.title}")
            self.console.print(f"[cyan]Link:[/cyan] {entry.link}")
            self.console.print(f"[italic]{entry.summary}[/italic]\n")
