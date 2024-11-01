from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from datetime import datetime
import requests
import signal
import sys
from email_service import EmailService
from rss_service import RSSService
from utils import fetch_7_day_weather, fetch_stock_data, show_top_stocks
from bot import chatbot_loop  

console = Console()
exit_requested = False  
confirm_exit = False    

email_service = EmailService()
rss_service = RSSService()

def handle_exit_signal(signal_received, frame):
    global confirm_exit
    confirm_exit = True

signal.signal(signal.SIGINT, handle_exit_signal)

def get_location():
    try:
        response = requests.get("https://ipinfo.io")
        response.raise_for_status()
        data = response.json()
        location = data["loc"].split(",")
        city = data["city"]
        latitude, longitude = float(location[0]), float(location[1])
        return {"city": city, "latitude": latitude, "longitude": longitude}
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error fetching location: {e}[/red] 🌐")
        return {"city": "Unknown", "latitude": 40.7128, "longitude": -74.0060}

def get_weather(latitude, longitude):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        weather = data["current_weather"]
        return f"{weather['temperature']}°C 🌡️"
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {e} ☁️"

def display_initial_layout():
    welcome_message = Panel(
        Align.center("[bold magenta]🌟  Welcome to Consolia 🌟[/bold magenta]\n[italic cyan] Your Terminal Workspace[/italic cyan]"),
        title="✨ Consolia ✨",
        border_style="magenta",
        padding=(1, 2),
    )
    console.print("\n", welcome_message)

    now = datetime.now()
    date_str = now.strftime("%A, %B %d, %Y - %H:%M")
    location_data = get_location()
    city = location_data["city"]
    latitude, longitude = location_data["latitude"], location_data["longitude"]
    weather_info = get_weather(latitude, longitude)

    console.print("\n[bold cyan]🌍  Current Session Details[/bold cyan]", style="bold underline")
    console.print(f"[bold]📅  Date:[/bold] {date_str}")
    console.print(f"[bold]📍  Location:[/bold] {city}")
    console.print(f"[bold]🌤️   Weather:[/bold] {weather_info}\n")
    console.print("[bold green]=============================================[/bold green]")

def display_options_menu():
    console.print("\n[bold yellow]🛠️   Options Menu:[/bold yellow]", style="bold underline")
    
    if not email_service.is_logged_in:
        console.print("[bold green]1.[/bold green] 🔑  Login (Gmail)")
        console.print("[bold green]2.[/bold green] 📖  View RSS Feeds")
        console.print("[bold green]3.[/bold green] 🤖  ChatBot")
        console.print("[bold green]4.[/bold green] 📈  View Stock Data")
        console.print("[bold green]5.[/bold green] ☁️   7-Day Weather Forecast")
        console.print("[bold green]6.[/bold green] 🚪  Exit")
    else:
        console.print("[bold green]1.[/bold green] 📧  Check Email")
        console.print("[bold green]2.[/bold green] ✉️   Send Email")
        console.print("[bold green]3.[/bold green] 🖊️   Set Email Signature")  
        console.print("[bold green]4.[/bold green] 🔒  Logout")

    console.print("[bold green]=============================================[/bold green]")


def stock_option():
    while True:
        console.print("\n[bold yellow]Stock Menu:[/bold yellow]")
        console.print("[bold green]1.[/bold green] 📊 Choose from Top 10 Stocks")
        console.print("[bold green]2.[/bold green] 🔍 Search for a Stock by Symbol")
        console.print("[bold green]3.[/bold green] 🔙 Go Back to Main Menu")

        choice = console.input("\nChoose an option (1-3): ")
        if choice == '1':
            show_top_stocks()
        elif choice == '2':
            symbol = console.input("🔍 Enter Stock Symbol (e.g., AAPL): ").strip().upper()
            stock_data = fetch_stock_data(symbol)
            console.print(stock_data)
        elif choice == '3':
            break
        else:
            console.print("[red]Invalid choice! Please enter a number between 1 and 3.[/red]")

def weather_option():
    while True:
        console.print("\n[bold yellow]Weather Menu:[/bold yellow]")
        console.print("[bold green]1.[/bold green] 🌦️  Enter a New City for Weather")
        console.print("[bold green]2.[/bold green] 🔙 Go Back to Main Menu")
        
        choice = console.input("\nChoose an option (1-2): ")
        if choice == '1':
            city = console.input("🏙️ [bold cyan]Enter City for Weather Forecast: [/bold cyan]")
            forecast = fetch_7_day_weather(city)
            console.print(f"[bold green]7-Day Weather Forecast for {city}:[/bold green] \n{forecast}")
        elif choice == '2':
            break
        else:
            console.print("[red]Invalid choice! Please enter a number between 1 and 2.[/red]")

def main():
    global exit_requested, confirm_exit
    display_initial_layout()  

    while True:
        try:
            if confirm_exit:
                confirm_exit = False  
                answer = console.input("[bold red]Are you sure you want to quit? (y/n): [/bold red]")
                if answer.lower() == 'y':
                    console.print("[bold red]Goodbye![/bold red] 👋")
                    sys.exit(0)

            display_options_menu()
            option = console.input("\nChoose an option: ")
            handle_option(option)

        except EOFError:
            console.print("\n[bold red]Input stream closed unexpectedly. Exiting program.[/bold red] 👋")
            sys.exit(0)

def handle_option(option):
    if option == '1':
        if not email_service.is_logged_in:
            email_service.login()  
        else:
            email_service.fetch_mail_ids()  
    elif option == '2':
        if not email_service.is_logged_in:
            rss_service.display_all_feeds()  
        else:
            to = console.input("📬 [bold cyan]Recipient Email Address: [/bold cyan]")
            subject = console.input("📜 [bold cyan]Subject: [/bold cyan]")
            message = console.input("📝 [bold cyan]Message: [/bold cyan]")
            email_service.send_mail(to, subject, message)  
    elif option == '3':
        if not email_service.is_logged_in:
            chatbot_loop()  
        else:
            email_service.set_signature()  
    elif option == '4':
        if not email_service.is_logged_in:
            stock_option()  
        else:
            email_service.logout()  
    elif option == '5' and not email_service.is_logged_in:
        weather_option()  
    elif option == '6' and not email_service.is_logged_in:
        console.print("[bold red]Exiting program...[/bold red] 👋")
        sys.exit(0)
    else:
        console.print("[red]Invalid option! Please select a valid option.[/red] 🚫")

if __name__ == "__main__":
    main()
