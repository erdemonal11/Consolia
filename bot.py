from rich.console import Console
import pyttsx3
import spacy
from datetime import datetime
from utils import fetch_7_day_weather, fetch_stock_data, fetch_news, fetch_joke

console = Console()
nlp = spacy.load("en_core_web_sm")
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 150)

memory = {"last_city": None, "last_stock": None, "last_topic": None}
speaking_mode = False

def speak_text(text):
    if speaking_mode:
        tts_engine.say(text)
        tts_engine.runAndWait()

def interpret_entities(doc):
    entities = {"city": None, "stock": None, "topic": None}
    for ent in doc.ents:
        if ent.label_ == "GPE":
            entities["city"] = ent.text
        elif ent.label_ in ["ORG", "PRODUCT"]:
            entities["stock"] = ent.text.upper()
        elif ent.label_ in ["PERSON", "NORP", "EVENT"]:
            entities["topic"] = ent.text
    return entities

def clean_stock_request(user_input):
    if "stock of" in user_input:
        return user_input.replace("stock of", "").strip().upper()
    return user_input.upper()

def chatbot_response(user_input):
    global speaking_mode
    user_input = user_input.strip().lower()
    doc = nlp(user_input)
    entities = interpret_entities(doc)

    if user_input == "help":
        response = (
            "[bold blue]🤖 Here are some commands you can try:[/bold blue]\n"
            "- [yellow]'weather in [city]'[/yellow]: Get the 7-day weather forecast.\n"
            "- [yellow]'stock of [symbol]'[/yellow]: Get the latest stock data.\n"
            "- [yellow]'current time'[/yellow]: Find out the current time.\n"
            "- [yellow]'news about [topic]'[/yellow]: Get news on a specific topic.\n"
            "- [yellow]'tell me a joke'[/yellow]: Hear a joke!\n"
            "- [yellow]'enable speaking mode'[/yellow]: Enable text-to-speech.\n"
            "- [yellow]'disable speaking mode'[/yellow]: Disable text-to-speech.\n"
            "[bold green]Type 'help' if you're not sure![/bold green]"
        )
        speak_text(response)
        return response

    if any(greet in user_input for greet in ["hi", "hello", "hey"]):
        response = "[bold magenta]👋 Hello! How can I assist you today?[/bold magenta]"
        speak_text(response)
        return response

    if "enable speaking mode" in user_input:
        speaking_mode = True
        return "[bold green]🔊 Speaking mode enabled! I will now read responses aloud.[/bold green]"
    elif "disable speaking mode" in user_input:
        speaking_mode = False
        return "[bold red]🔇 Speaking mode disabled. I'll respond with text only.[/bold red]"

    if "how are you" in user_input:
        response = "[bold magenta]😊 I'm here and ready to help! What can I do for you?[/bold magenta]"
        speak_text(response)
        return response

    is_weather_request = "weather" in user_input
    is_stock_request = "stock" in user_input or entities["stock"]

    if is_weather_request or (entities["city"] and not is_stock_request):
        city = entities["city"] if entities["city"] else memory["last_city"]
        if city:
            memory["last_city"] = city
            forecast = fetch_7_day_weather(city)
            response = f"[bold cyan]🌤️ Here’s the weather for {city.capitalize()}:[/bold cyan]\n📅 [italic]7-Day Forecast[/italic]\n{forecast}"
            speak_text(response)
            return response
        response = "[yellow]⚠️ Please specify a city for the weather update.[/yellow]"
        speak_text(response)
        return response

    if is_stock_request:
        stock_symbol = clean_stock_request(user_input) if not entities["stock"] else entities["stock"]
        if stock_symbol:
            memory["last_stock"] = stock_symbol
            stock_data = fetch_stock_data(stock_symbol)
            response = (
                f"[bold cyan]📈 Here’s the latest on {stock_symbol}:[/bold cyan]\n{stock_data}"
                if stock_data else f"[bold red]⚠️ No data available for '{stock_symbol}'. Please check the stock symbol and try again.[/bold red]"
            )
            speak_text(response)
            return response
        response = "[yellow]⚠️ Please provide a stock symbol to get the latest price.[/yellow]"
        speak_text(response)
        return response

    if "news" in user_input or entities["topic"]:
        topic = entities["topic"] if entities["topic"] else user_input.capitalize()
        if topic:
            memory["last_topic"] = topic
            news = fetch_news(topic)
            response = f"[bold cyan]📰 Here’s the latest news on '{topic.capitalize()}':[/bold cyan]\n{news}" if news else f"[bold red]⚠️ Couldn't find news on '{topic}'.[/bold red]"
            speak_text(response)
            return response
        response = "[yellow]⚠️ Could you specify a topic for the news update?[/yellow]"
        speak_text(response)
        return response

    if "joke" in user_input or "fun fact" in user_input:
        joke = fetch_joke()
        response = joke if joke else "[yellow]😄 I couldn't fetch a joke right now, but I've got plenty stored up![/yellow]"
        speak_text(response)
        return response

    if "time" in user_input:
        current_time = datetime.now().strftime("%I:%M %p on %A, %B %d, %Y")
        response = f"[bold cyan]🕒 The current time is {current_time}.[/bold cyan]"
        speak_text(response)
        return response

    response = (
        "[bold red]🤔 I’m not sure I understood. Try commands like:[/bold red]\n"
        "- [yellow]'weather in [city]'[/yellow]\n"
        "- [yellow]'stock of [symbol]'[/yellow]\n"
        "- [yellow]'current time'[/yellow]\n"
        "- [yellow]'news about [topic]'[/yellow]\n"
        "- [yellow]'tell me a joke'[/yellow]\n"
        "[green]Type 'help' if you're not sure![/green]"
    )
    speak_text(response)
    return response


def chatbot_loop():
    console.print("[bold green]=============================================[/bold green]")
    console.print("[bold magenta]👋 Hello, I’m Consolia! Your friendly assistant bot![/bold magenta]")
    console.print("[italic cyan]Type 'help' to see what I can do or 'exit' to leave the chat.[/italic cyan]")
    console.print("[bold green]=============================================[/bold green]\n")

    while True:
        console.print("[bold green]=============================================[/bold green]")
        user_input = console.input("[bold blue]You:[/bold blue] ")
        if user_input.lower() in ["exit", "quit"]:
            console.print("[bold red]👋 Goodbye! It was nice assisting you.[/bold red]")
            break
        response = chatbot_response(user_input)
        console.print(response)
