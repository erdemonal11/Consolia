# bot.py
from rich.console import Console
from random import choice
import spacy
from datetime import datetime
from utils import fetch_7_day_weather, fetch_stock_data

console = Console()
nlp = spacy.load("en_core_web_sm")

# Memory to hold last context for follow-up queries
memory = {"last_city": None, "last_stock": None, "last_topic": None}

# Multiple jokes for variety
jokes = [
    "Why did the developer go broke? Because they used up all their cache! 😂",
    "Why do Java developers wear glasses? Because they don’t C#! 🤓",
    "How many programmers does it take to change a light bulb? None—it’s a hardware problem! 💡",
]

def introduction():
    """Introduce ConsoliaBot with a simple, conversational UI."""
    console.print("\n🌟 [bold cyan]Welcome to ConsoliaBot[/bold cyan] 🌟")
    console.print(
        "\nHello! I’m ConsoliaBot, your interactive assistant.\n"
        "I can help you with:\n"
        "- Weather updates 🌦️\n"
        "- Stock prices 📈\n"
        "- News updates 📰\n"
        "- Current time ⏰\n"
        "- Fun trivia and jokes 🎉\n"
        "\nJust ask away! Type 'help' for guidance or 'exit' to leave.\n"
    )

def interpret_entities(doc):
    """Extract city, stock symbol, and topic from user input."""
    entities = {"city": None, "stock": None, "topic": None}
    for ent in doc.ents:
        if ent.label_ == "GPE":  # Location for weather
            entities["city"] = ent.text
        elif ent.label_ in ["ORG", "PRODUCT"]:  # Stock symbols
            entities["stock"] = ent.text.upper()
        elif ent.label_ in ["PERSON", "NORP", "EVENT"]:  # News topics
            entities["topic"] = ent.text
    return entities

def chatbot_response(user_input):
    """Generate responses, handling both initial and follow-up queries."""
    user_input = user_input.strip().lower()  # Lowercase and strip input for consistency
    doc = nlp(user_input)
    entities = interpret_entities(doc)

    # Detect user intent based on keywords
    is_weather_request = "weather" in user_input
    is_news_request = "news" in user_input
    is_stock_request = "stock" in user_input or entities["stock"]

    # Handle greetings and basic intros
    if any(greet in user_input for greet in ["hi", "hello", "hey"]):
        return "Hello! 👋 How can I assist you today?"
    if "how are you" in user_input:
        return "I'm here and ready to help! 😊 What can I do for you?"

    # Weather Request
    if is_weather_request or (entities["city"] and not is_news_request):
        city = entities["city"] if entities["city"] else memory["last_city"]
        if city:
            memory["last_city"] = city
            forecast = fetch_7_day_weather(city)
            return f"Here’s the weather for {city.capitalize()}:\n📅 7-Day Forecast\n{forecast}"
        return "Please specify a city for the weather update."

    # Stock Price Request
    if is_stock_request:
        stock_symbol = entities["stock"] if entities["stock"] else user_input.split()[-1].upper()
        if stock_symbol:
            memory["last_stock"] = stock_symbol  # Store stock symbol for follow-ups
            stock_data = fetch_stock_data(stock_symbol)
            return f"Here’s the latest on {stock_symbol}:\n{stock_data}" if stock_data else f"Couldn't find data for '{stock_symbol}'."
        return "Please provide a stock symbol to get the latest price."

    # Follow-Up for Last Stock Query (if no new context given)
    if memory["last_stock"] and user_input.upper() == memory["last_stock"]:
        stock_data = fetch_stock_data(memory["last_stock"])
        return f"Here's the latest on {memory['last_stock']}:\n{stock_data}" if stock_data else f"Couldn't retrieve data for '{memory['last_stock']}'."

    # Current Time
    if "time" in user_input:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"The current time is {current_time} ⏰."

    # News Request
    if is_news_request or entities["topic"]:
        topic = entities["topic"] if entities["topic"] else memory["last_topic"]
        if topic:
            memory["last_topic"] = topic
            return f"Fetching the latest news on '{topic.capitalize()}'... 📰 [Mock News Data]"
        return "Could you specify a topic for the news update?"

    # Fun Trivia or Joke
    if "joke" in user_input or "fun fact" in user_input:
        return choice(jokes)

    # Help
    if "help" in user_input:
        return (
            "Here's what I can assist you with:\n\n"
            "- 'weather in [city]': Get a weather forecast\n"
            "- 'stock of [symbol]': Check stock prices\n"
            "- 'current time': See the current time\n"
            "- 'news about [topic]': Get the latest news\n"
            "- 'tell me a joke': For some humor\n\n"
            "Type 'exit' anytime to leave."
        )

    # Fallback Response
    return (
        "I’m not sure I understood. Try commands like:\n"
        "- 'weather in [city]'\n"
        "- 'stock of [symbol]'\n"
        "- 'current time'\n"
        "- 'news about [topic]'\n"
        "- 'tell me a joke'\n\nType 'help' if you're not sure!"
    )



def chatbot_loop():
    """Run the interactive chatbot loop with refined UI and better parsing."""
    introduction()

    console.print("[dim]Type 'help' if you're unsure or 'exit' to leave the chatbot.[/dim]\n")

    while True:
        user_input = console.input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            console.print("[bold red]Goodbye![/bold red] 👋 It was nice assisting you.")
            break
        response = chatbot_response(user_input)
        console.print(response)
