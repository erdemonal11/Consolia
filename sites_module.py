# sites_module.py
from rich.console import Console
from rich.table import Table

console = Console()

def show_sites():
    """Displays a list of recommended sites."""
    console.print("Displaying recommended sites:")

    table = Table(title="Recommended Sites")
    table.add_column("Site", style="bold")
    table.add_column("Description")

    # Example sites (replace with actual sites as needed)
    sites = [
        ("Python.org", "The official website for Python programming language."),
        ("TechCrunch", "Latest technology news and startup stories."),
        ("GitHub", "A platform for hosting and collaborating on code."),
    ]

    for site, description in sites:
        table.add_row(site, description)

    console.print(table)
