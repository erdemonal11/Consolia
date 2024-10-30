import os
import requests
from yahooquery import Ticker
from rich.console import Console
from rich.progress import Progress

console = Console()

TOP_STOCKS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "FB", "BRK.B", "V", "JNJ", "WMT"]

def fetch_7_day_weather(city):
    console.print(f"\n🌦️ [bold cyan]Fetching weather for {city}...[/bold cyan]")
    try:
        location_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}"
        location_response = requests.get(location_url)
        location_response.raise_for_status()
        location_data = location_response.json()

        if not location_data.get("results"):
            return f"No results found for city: {city}"

        latitude = location_data["results"][0]["latitude"]
        longitude = location_data["results"][0]["longitude"]

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=temperature_2m_min,temperature_2m_max,windspeed_10m_max,weathercode&timezone=auto"
        weather_response = requests.get(weather_url)
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        weather_icons = {"sun": "☀️", "cloud": "☁️", "rain": "🌧️", "snow": "❄️", "wind": "💨"}

        def get_weather_icon(code):
            if code in range(0, 3): return weather_icons["sun"]
            if code in range(3, 5): return weather_icons["cloud"]
            if code in range(5, 7): return weather_icons["rain"]
            if code == 7: return weather_icons["snow"]
            if code >= 8: return weather_icons["wind"]
            return "🌡️"

        forecast = f"\n📅 [bold magenta]7-Day Weather Forecast for {city.capitalize()}[/bold magenta]\n"
        for day, min_temp, max_temp, wind_speed, weather_code in zip(
            weather_data["daily"]["time"],
            weather_data["daily"]["temperature_2m_min"],
            weather_data["daily"]["temperature_2m_max"],
            weather_data["daily"]["windspeed_10m_max"],
            weather_data["daily"]["weathercode"]
        ):
            icon = get_weather_icon(weather_code)
            forecast += (f"{day}: Min {min_temp}°C, Max {max_temp}°C, Wind: {wind_speed} km/h "
                         f"{icon}\n")

        return forecast

    except requests.RequestException as e:
        return f"[red]Error fetching weather data: {e}[/red]"

def fetch_news(topic):
    api_key = os.getenv("NEWS_API_KEY")
    url = f"https://newsapi.org/v2/everything?q={topic}&language=en&pageSize=5&apiKey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        news = ""
        for article in articles:
            news += f"\n📰 {article['title']} - {article['source']['name']}\n"
            news += f"{article['description']}\n{article['url']}\n"
        return news if news else "No news articles found for the specified topic."
    except requests.RequestException as e:
        return f"[red]Error fetching news: {e}[/red]"

def fetch_stock_data(symbol):
    try:
        console.print(f"\n🔍 [bold cyan]Searching for {symbol} stock data...[/bold cyan]")
        ticker = Ticker(symbol)
        stock_info = ticker.summary_detail.get(symbol)

        if stock_info is None or isinstance(stock_info, str):
            return f"[red]No data available for {symbol}. Please check the stock symbol and try again.[/red]"

        price = stock_info.get("regularMarketPrice", "Unavailable")
        currency = stock_info.get("currency", "USD")
        previous_close = stock_info.get("previousClose", "Unavailable")
        open_price = stock_info.get("open", "Unavailable")
        day_high = stock_info.get("dayHigh", "Unavailable")
        day_low = stock_info.get("dayLow", "Unavailable")

        return (
            f"\n📈 [bold magenta]{symbol} Stock Data[/bold magenta]\n"
            f"Current Price: {price} {currency}\n"
            f"Previous Close: {previous_close} {currency}\n"
            f"Open: {open_price} {currency}\n"
            f"Day High: {day_high} {currency}\n"
            f"Day Low: {day_low} {currency}"
        )

    except Exception as e:
        return f"[red]Error fetching stock data for {symbol}: {e}[/red]"

def show_top_stocks():
    console.print("\n📊 [bold yellow]Fetching Top 10 Stocks with Prices...[/bold yellow]")
    stock_info = []

    with Progress(console=console) as progress:
        task = progress.add_task("[cyan]Loading stock data...", total=len(TOP_STOCKS))

        for symbol in TOP_STOCKS:
            ticker = Ticker(symbol)
            try:
                price_data = ticker.price.get(symbol)
                if isinstance(price_data, dict):
                    price = price_data.get("regularMarketPrice", "Unavailable")
                else:
                    price = "Unavailable"
                stock_info.append(f"{symbol}: {price} USD")
            except (AttributeError, TypeError, KeyError):
                stock_info.append(f"{symbol}: Unavailable")
            progress.update(task, advance=1)

    console.print(" | ".join(stock_info))

def fetch_joke():
    joke_url = "https://v2.jokeapi.dev/joke/Any"
    try:
        response = requests.get(joke_url)
        response.raise_for_status()
        data = response.json()
        if data["type"] == "single":
            return data["joke"]
        else:
            return f"{data['setup']} ... {data['delivery']}"
    except requests.RequestException as e:
        return f"[red]Error fetching joke: {e}[/red]"
