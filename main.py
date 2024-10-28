# main.py
import os
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from email_module import check_inbox
from rss_module import fetch_rss_feed
from sites_module import show_sites

console = Console()

def display_header():
    """Display a welcome message with Rich formatting."""
    console.clear()
    console.print("[bold cyan]Welcome to Consolia![/bold cyan]", justify="center")
    console.print("[bold]Terminal-based Social Media Interface[/bold]", justify="center")
    console.print("=" * 50)

def main_menu():
    """Main menu of the application."""
    while True:
        display_header()
        console.print("[1] Email")
        console.print("[2] RSS Feed")
        console.print("[3] Recommended Sites")
        console.print("[Q] Quit")

        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "Q"], default="Q").strip().upper()

        if choice == "1":
            email_module()
        elif choice == "2":
            rss_module()
        elif choice == "3":
            show_sites_module()
        elif choice == "Q":
            console.print("Exiting... Goodbye!")
            break

def email_module():
    """Prompt user for email login and display inbox."""
    console.print("\n[bold]Email Module[/bold]")
    email = Prompt.ask("Enter your email")
    password = Prompt.ask("Enter your password", password=True)

    console.print("[bold cyan]Checking inbox...[/bold cyan]")
    check_inbox(email, password)

    console.print("\nPress Enter to return to the main menu.")
    input()  # Wait for user to press Enter to return

def rss_module():
    """Fetch and display RSS feed articles."""
    console.print("\n[bold]RSS Feed Module[/bold]")
    rss_url = Prompt.ask("Enter the RSS feed URL", default="https://rss.cnn.com/rss/edition.rss")
    
    console.print("[bold cyan]Fetching RSS feed...[/bold cyan]")
    fetch_rss_feed(rss_url)

    console.print("\nPress Enter to return to the main menu.")
    input()  # Wait for user to press Enter to return

def show_sites_module():
    """Display recommended sites."""
    console.print("\n[bold]Recommended Sites[/bold]")
    show_sites()

    console.print("\nPress Enter to return to the main menu.")
    input()  # Wait for user to press Enter to return

if __name__ == "__main__":
    main_menu()
