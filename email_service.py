import imaplib
import smtplib
import re
from email.mime.text import MIMEText
from email.parser import BytesParser
from email.header import decode_header
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich import box

class EmailService:
    def __init__(self):
        self.console = Console()
        self.imap_server = 'imap.gmail.com'
        self.smtp_server = 'smtp.gmail.com'
        self.username = None
        self.password = None
        self.name = None
        self.is_logged_in = False
        self.page = 0
        self.page_size = 5
        self.mail_ids = []
        self.prompt_shown = False

    def setup_credentials(self):
        """Prompts the user to enter their email credentials only once per session."""
        if not self.prompt_shown:
            self.console.print("[yellow]Please enter your Gmail credentials. Note: Use an [bold]App Password[/bold] if you have two-factor authentication enabled.[/yellow]")
            self.console.print("[italic]For more info on App Passwords, visit [link=https://support.google.com/accounts/answer/185833]Google's App Password Guide[/link][/italic].")
            self.prompt_shown = True

        self.username = self.console.input("Gmail address: ")

        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.username):
            self.console.print("[red]Invalid email format. Please enter a valid email address (e.g., user@gmail.com).[/red]")
            self.username = None
            return self.setup_credentials()

        self.password = self.console.input("App Password (not your Gmail password): ", password=True)

    def login(self):
        """Logs in the user with provided credentials and retrieves their name."""
        self.setup_credentials()
        try:
            with imaplib.IMAP4_SSL(self.imap_server) as mail:
                mail.login(self.username, self.password)
                self.is_logged_in = True
                self.name = self.username.split("@")[0].title()
                self.console.print(f"[green]Hi, {self.name}! You are now logged in.[/green]")
        except imaplib.IMAP4.error:
            self.console.print("[red]Authentication Error:[/red] Invalid credentials. Make sure you are using an App Password.")
            self.username = self.password = None
            self.is_logged_in = False
        except Exception as e:
            self.console.print(f"[red]Error:[/red] {str(e)}")

    def logout(self):
        """Logs the user out by clearing stored credentials."""
        self.username = self.password = self.name = None
        self.is_logged_in = False
        self.console.print("[green]You have successfully logged out.[/green]")

    def fetch_mail_ids(self):
        """Fetches email IDs and displays the email list."""
        if not self.is_logged_in:
            self.console.print("[red]You need to log in first.[/red]")
            return

        try:
            with self.console.status("📧  Checking emails...", spinner="dots"):
                with imaplib.IMAP4_SSL(self.imap_server) as mail:
                    mail.login(self.username, self.password)
                    mail.select('inbox')
                    status, messages = mail.search(None, 'ALL')
                    self.mail_ids = messages[0].split()
                    total_emails = len(self.mail_ids)
                    self.page = 0
                    self.console.print(f"[green]Total emails:[/green] {total_emails}")
            self.display_emails()
        except imaplib.IMAP4.error:
            self.console.print("[red]Authentication Error:[/red] Invalid credentials.")
        except Exception as e:
            self.console.print(f"[red]Error:[/red] {str(e)}")

    def display_emails(self):
        """Displays a page of 5 emails at a time with pagination controls."""
        while True:
            start = self.page * self.page_size
            end = start + self.page_size
            page_mail_ids = self.mail_ids[max(0, len(self.mail_ids) - end): len(self.mail_ids) - start]

            self.console.print("[bold cyan]Emails (page {}/{}):[/bold cyan]".format(self.page + 1, (len(self.mail_ids) // self.page_size) + 1))
            
            for i, mail_id in enumerate(page_mail_ids, start=1):
                with imaplib.IMAP4_SSL(self.imap_server) as mail:
                    mail.login(self.username, self.password)
                    mail.select('inbox')
                    status, data = mail.fetch(mail_id, '(RFC822)')
                    email_message = BytesParser().parsebytes(data[0][1])

                    subject, encoding = decode_header(email_message.get("Subject", "No Subject"))[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8") if encoding else subject.decode()

                    from_address = email_message.get("From", "Unknown Sender")
                    self.console.print(Panel(
                        f"[bold]From:[/bold] {from_address}\n[bold]Subject:[/bold] {subject}",
                        title=f"📨 Email {i} Summary",
                        border_style="green",
                        box=box.ROUNDED
                    ))

            self.console.print("\n[bold cyan]Commands:[/bold cyan] [blue]next[/blue] | [blue]prev[/blue] | [blue]select <number>[/blue] | [blue]exit[/blue]")
            
            if not self.pagination_controls(page_mail_ids):
                break

    def pagination_controls(self, page_mail_ids):
        """Handles pagination and selection of emails."""
        while True:
            command = self.console.input("\nEnter command: ").strip().lower()

            if command == "next":
                if (self.page + 1) * self.page_size < len(self.mail_ids):
                    self.page += 1
                    return True
                else:
                    self.console.print("[red]No more pages.[/red]")
            elif command == "prev":
                if self.page > 0:
                    self.page -= 1
                    return True
                else:
                    self.console.print("[red]No previous pages.[/red]")
            elif command.startswith("select "):
                try:
                    index = int(command.split(" ")[1]) - 1
                    if 0 <= index < len(page_mail_ids):
                        self.display_email_detail(page_mail_ids[index])
                    else:
                        self.console.print("[red]Invalid selection. Choose a number from the current page.[/red]")
                except (IndexError, ValueError):
                    self.console.print("[red]Invalid command. Use 'select <number>' to choose an email.[/red]")
            elif command == "exit":
                return False
            else:
                self.console.print("[red]Invalid command.[/red]")

    def display_email_detail(self, mail_id):
        """Displays the full details of a selected email."""
        try:
            with imaplib.IMAP4_SSL(self.imap_server) as mail:
                mail.login(self.username, self.password)
                mail.select('inbox')
                status, data = mail.fetch(mail_id, '(RFC822)')
                email_message = BytesParser().parsebytes(data[0][1])

                subject, encoding = decode_header(email_message.get("Subject", "No Subject"))[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8") if encoding else subject.decode()

                from_address = email_message.get("From", "Unknown Sender")
                body = email_message.get_payload(decode=True).decode("utf-8", errors="ignore") if email_message.get_payload(decode=True) else "No content"

                self.console.print(Panel(
                    f"[bold]From:[/bold] {from_address}\n[bold]Subject:[/bold] {subject}\n\n[bold]Message:[/bold]\n{body}",
                    title="📨 Full Email",
                    border_style="cyan",
                    box=box.ROUNDED
                ))

        except Exception as e:
            self.console.print(f"[red]Error displaying email details: {e}[/red]")

    def send_mail(self, to, subject, message):
        """Sends an email with a loading animation."""
        if not self.is_logged_in:
            self.console.print("[red]You need to log in first.[/red]")
            return

        try:
            with self.console.status("✉️  Sending email...", spinner="dots"):
                msg = MIMEText(message)
                msg['Subject'] = subject
                msg['From'] = self.username
                msg['To'] = to

                with smtplib.SMTP_SSL(self.smtp_server) as server:
                    server.login(self.username, self.password)
                    server.sendmail(self.username, to, msg.as_string())

            self.console.print("[green]Email sent successfully![/green]")
        except smtplib.SMTPAuthenticationError:
            self.console.print("[red]Authentication Error:[/red] Invalid credentials.")
        except Exception as e:
            self.console.print(f"[red]Error:[/red] {str(e)}")
