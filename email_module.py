# email_module.py
import imaplib
from email.message import EmailMessage
from rich.console import Console

console = Console()

def check_inbox(email, password):
    try:
        mail = imaplib.IMAP4_SSL("imap.example.com")  # Replace with actual email server
        mail.login(email, password)
        mail.select("inbox")

        result, data = mail.search(None, "ALL")
        mail_ids = data[0].split()
        latest_email_id = mail_ids[-1] if mail_ids else None

        if latest_email_id:
            result, data = mail.fetch(latest_email_id, "(RFC822)")
            raw_email = data[0][1].decode("utf-8", errors="ignore") if data[0] else "No data"
            console.print(f"[dim]{raw_email}[/dim]")
        else:
            console.print("[yellow]No emails found in inbox.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error checking inbox: {e}[/red]")
