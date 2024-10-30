import feedparser
import json
import os
from rich.console import Console
from rich.panel import Panel
from rich import box

class RSSService:
    def __init__(self, storage_file="rss_feeds.json"):
        self.console = Console()
        self.storage_file = storage_file
        self.favorites_file = "rss_favorites.json"  
        self.feeds = self.load_feeds()
        self.favorites = self.load_favorites()

    def load_feeds(self):
        if os.path.exists(self.storage_file):
            with open(self.storage_file, "r") as file:
                return json.load(file)
        return {
            "suggested": {
                "BBC News": "http://feeds.bbci.co.uk/news/rss.xml",
                "TechCrunch": "http://feeds.feedburner.com/TechCrunch/",
                "New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
                "CNN": "http://rss.cnn.com/rss/edition.rss",
                "NBC News": "http://feeds.nbcnews.com/feeds/worldnews"
            },
            "custom": {}
        }

    def load_favorites(self):
        if os.path.exists(self.favorites_file):
            with open(self.favorites_file, "r") as file:
                return json.load(file)
        return []

    def save_feeds(self):
        with open(self.storage_file, "w") as file:
            json.dump(self.feeds, file, indent=4)

    def save_favorites(self):
        with open(self.favorites_file, "w") as file:
            json.dump(self.favorites, file, indent=4)

    def display_feed(self, url):
        self.console.print(f"[blue]Fetching RSS feed from: {url}[/blue]")
        feed = feedparser.parse(url)

        if feed.entries:
            page = 0
            page_size = 5
            while True:
                start = page * page_size
                end = start + page_size
                entries = feed.entries[start:end]

                total_pages = (len(feed.entries) - 1) // page_size + 1
                self.console.print(f"[bold cyan]RSS Entries (Page {page + 1}/{total_pages}):[/bold cyan]")
                for i, entry in enumerate(entries, start=1):
                    self.console.print(Panel(
                        f"[bold green]{i + start}. Title:[/bold green] {entry.title}\n"
                        f"[cyan]Link:[/cyan] {entry.link}",
                        title="📰 RSS Entry Summary",
                        border_style="green",
                        box=box.ROUNDED
                    ))

                self.console.print("\n[bold yellow]Commands:[/bold yellow] [blue]next[/blue] | [blue]prev[/blue] | [blue]read <number>[/blue] | [blue]go <page>[/blue] | [blue]exit[/blue]")
                command = self.console.input("\nEnter command: ").strip().lower()

                if command == "next":
                    if end < len(feed.entries):
                        page += 1
                    else:
                        self.console.print("[red]No more pages.[/red]")
                elif command == "prev":
                    if page > 0:
                        page -= 1
                    else:
                        self.console.print("[red]No previous pages.[/red]")
                elif command.startswith("go "):
                    try:
                        go_to_page = int(command.split(" ")[1]) - 1
                        if 0 <= go_to_page < total_pages:
                            page = go_to_page
                        else:
                            self.console.print("[red]Invalid page number.[/red]")
                    except ValueError:
                        self.console.print("[red]Invalid page number.[/red]")
                elif command.startswith("read "):
                    try:
                        entry_index = int(command.split(" ")[1]) - 1
                        if 0 <= entry_index < len(feed.entries):
                            self.display_full_entry(feed.entries[entry_index])
                        else:
                            self.console.print("[red]Invalid selection. Please choose a valid number.[/red]")
                    except (IndexError, ValueError):
                        self.console.print("[red]Invalid command. Use 'read <number>' to view an entry.[/red]")
                elif command == "exit":
                    break
                else:
                    self.console.print("[red]Invalid command.[/red]")
        else:
            self.console.print("[red]No entries found or unable to fetch the feed.[/red]")

    def display_full_entry(self, entry, is_favorite=False):
        self.console.print(Panel(
            f"[bold green]Title:[/bold green] {entry.get('title')}\n"
            f"[cyan]Link:[/cyan] {entry.get('link')}\n\n"
            f"[italic]{entry.get('summary')}[/italic]",
            title="📜 Full RSS Entry",
            border_style="cyan",
            box=box.ROUNDED
        ))

        if not is_favorite:
            self.console.print("\n[bold yellow]Commands:[/bold yellow] [blue]favorite[/blue] | [blue]back[/blue]")
        else:
            self.console.print("\n[bold yellow]Commands:[/bold yellow] [blue]remove favorite[/blue] | [blue]back[/blue]")

        command = self.console.input("\nEnter command: ").strip().lower()

        if command == "favorite" and not is_favorite:
            if not any(fav['link'] == entry['link'] for fav in self.favorites):
                self.favorites.append({
                    "title": entry.get("title"),
                    "link": entry.get("link"),
                    "summary": entry.get("summary")
                })
                self.save_favorites()
                self.console.print("[green]Added to favorites![/green]")
            else:
                self.console.print("[yellow]Already in favorites.[/yellow]")
            self.display_full_entry(entry, is_favorite=True)
        elif command == "remove favorite" and is_favorite:
            self.favorites = [fav for fav in self.favorites if fav['link'] != entry['link']]
            self.save_favorites()
            self.console.print("[green]Removed from favorites![/green]")

    def display_all_feeds(self):
        while True:
            self.console.print("\n[bold cyan]Available RSS Feeds:[/bold cyan]")
            all_feeds = {**self.feeds["suggested"], **self.feeds["custom"]}
            for i, (name, url) in enumerate(all_feeds.items(), 1):
                self.console.print(f"[bold green]{i}.[/bold green] {name} - {url}")

            self.console.print("\n[bold yellow]Commands:[/bold yellow] [blue]view <number>[/blue] | [blue]add[/blue] | [blue]edit <number>[/blue] | [blue]delete <number>[/blue] | [blue]favorites[/blue] | [blue]exit[/blue]")
            command = self.console.input("\nEnter command: ").strip().lower()

            if command.startswith("view "):
                try:
                    index = int(command.split(" ")[1]) - 1
                    url = list(all_feeds.values())[index]
                    self.display_feed(url)
                except (IndexError, ValueError):
                    self.console.print("[red]Invalid selection. Please choose a valid number.[/red]")

            elif command == "add":
                name = self.console.input("Enter name for the new RSS feed: ").strip()
                url = self.console.input("Enter RSS feed URL: ").strip()
                if name and url:
                    self.feeds["custom"][name] = url
                    self.save_feeds()
                    self.console.print(f"[green]RSS feed '{name}' added successfully.[/green]")
                else:
                    self.console.print("[red]Name and URL are required.[/red]")

            elif command.startswith("edit "):
                try:
                    index = int(command.split(" ")[1]) - 1
                    key = list(all_feeds.keys())[index]
                    if key in self.feeds["suggested"]:
                        self.console.print("[red]Cannot edit suggested feeds.[/red]")
                    else:
                        new_name = self.console.input(f"Enter new name for '{key}' (or press Enter to keep the current name): ").strip() or key
                        new_url = self.console.input(f"Enter new URL for '{key}' (or press Enter to keep the current URL): ").strip() or self.feeds["custom"][key]
                        del self.feeds["custom"][key]
                        self.feeds["custom"][new_name] = new_url
                        self.save_feeds()
                        self.console.print(f"[green]RSS feed '{new_name}' updated successfully.[/green]")
                except (IndexError, ValueError):
                    self.console.print("[red]Invalid selection. Please choose a valid number.[/red]")

            elif command.startswith("delete "):
                try:
                    index = int(command.split(" ")[1]) - 1
                    key = list(all_feeds.keys())[index]
                    if key in self.feeds["suggested"]:
                        self.console.print("[red]Cannot delete suggested feeds.[/red]")
                    else:
                        del self.feeds["custom"][key]
                        self.save_feeds()
                        self.console.print(f"[green]RSS feed '{key}' deleted successfully.[/green]")
                except (IndexError, ValueError):
                    self.console.print("[red]Invalid selection. Please choose a valid number.[/red]")

            elif command == "favorites":
                self.display_favorites()

            elif command == "exit":
                break
            else:
                self.console.print("[red]Invalid command. Please try again.[/red]")

    def display_favorites(self):
        if not self.favorites:
            self.console.print("[yellow]No favorites found.[/yellow]")
            return

        page = 0
        page_size = 5
        total_pages = (len(self.favorites) - 1) // page_size + 1
        while True:
            start = page * page_size
            end = start + page_size
            entries = self.favorites[start:end]

            self.console.print(f"[bold cyan]Favorite Entries (Page {page + 1}/{total_pages}):[/bold cyan]")
            for i, entry in enumerate(entries, start=1):
                self.console.print(Panel(
                    f"[bold green]{i + start}. Title:[/bold green] {entry['title']}\n"
                    f"[cyan]Link:[/cyan] {entry['link']}",
                    title="⭐ Favorite Entry",
                    border_style="yellow",
                    box=box.ROUNDED
                ))

            self.console.print("\n[bold yellow]Commands:[/bold yellow] [blue]next[/blue] | [blue]prev[/blue] | [blue]go <page>[/blue] | [blue]read <number>[/blue] | [blue]remove <number>[/blue] | [blue]exit[/blue]")
            command = self.console.input("\nEnter command: ").strip().lower()

            if command == "next":
                if end < len(self.favorites):
                    page += 1
                else:
                    self.console.print("[red]No more pages.[/red]")
            elif command == "prev":
                if page > 0:
                    page -= 1
                else:
                    self.console.print("[red]No previous pages.[/red]")
            elif command.startswith("go "):
                try:
                    go_to_page = int(command.split(" ")[1]) - 1
                    if 0 <= go_to_page < total_pages:
                        page = go_to_page
                    else:
                        self.console.print("[red]Invalid page number.[/red]")
                except ValueError:
                    self.console.print("[red]Invalid page number.[/red]")
            elif command.startswith("read "):
                try:
                    index = int(command.split(" ")[1]) - 1
                    if 0 <= index < len(entries):
                        self.display_full_entry(entries[index], is_favorite=True)
                    else:
                        self.console.print("[red]Invalid selection. Choose a valid favorite to read.[/red]")
                except (IndexError, ValueError):
                    self.console.print("[red]Invalid command. Use 'read <number>' to view a favorite entry.[/red]")
            elif command.startswith("remove "):
                try:
                    index = int(command.split(" ")[1]) - 1
                    if 0 <= index < len(entries):
                        removed = self.favorites.pop(start + index)
                        self.save_favorites()
                        self.console.print(f"[green]Removed '{removed['title']}' from favorites.[/green]")
                    else:
                        self.console.print("[red]Invalid selection. Choose a valid favorite to remove.[/red]")
                except (IndexError, ValueError):
                    self.console.print("[red]Invalid command. Use 'remove <number>' to remove a favorite entry.[/red]")
            elif command == "exit":
                break
            else:
                self.console.print("[red]Invalid command. Please try again.[/red]")
