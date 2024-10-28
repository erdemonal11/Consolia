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
        self.imap_server = 'imap.gmail.com'  # Fixed IMAP server for Gmail
        self.smtp_server = 'smtp.gmail.com'  # Fixed SMTP server for Gmail
        self.username = None
        self.password = None
        self.page = 0
        self.page_size = 5
        self.mail_ids = []
        self.is_logged_in = False
        self.prompt_shown = False  # Flag to track if the App Password prompt has been shown

    def setup_credentials(self):
        """Prompts the user to enter their email credentials only once per session."""
        if not self.is_logged_in:
            if not self.prompt_shown:
                self.console.print("[yellow]Please enter your Gmail credentials. Note: Use an [bold]App Password[/bold] if you have two-factor authentication enabled.[/yellow]")
                self.console.print("[italic]For more info on App Passwords, visit [link=https://support.google.com/accounts/answer/185833]Google's App Password Guide[/link][/italic].")
                self.prompt_shown = True  # Set prompt_shown to True after the first display

            self.username = self.console.input("Gmail address: ")

            # Validate email format
            if not re.match(r"[^@]+@[^@]+\.[^@]+", self.username):
                self.console.print("[red]Invalid email format. Please enter a valid email address (e.g., user@gmail.com).[/red]")
                self.username = None  # Reset username to prompt again
                return self.setup_credentials()  # Re-run credentials setup

            self.password = self.console.input("App Password (not your Gmail password): ", password=True)
            self.is_logged_in = True

    def logout(self):
        """Logs the user out by clearing stored credentials."""
        self.username = None
        self.password = None
        self.is_logged_in = False
        self.console.print("[green]You have successfully logged out.[/green]")

    def fetch_mail_ids(self):
        """Fetches email IDs and displays the email list with a loading animation for the initial fetch only."""
        self.setup_credentials()  # Ensure credentials are set up only once
        try:
            with self.console.status("📧  Checking emails...", spinner="dots"):
                with imaplib.IMAP4_SSL(self.imap_server) as mail:
                    mail.login(self.username, self.password)
                    mail.select('inbox')
                    
                    # Search all emails
                    status, messages = mail.search(None, 'ALL')
                    self.mail_ids = messages[0].split()
                    total_emails = len(self.mail_ids)
                    self.page = 0  # Start on the first page
                    self.console.print(f"[green]Total emails:[/green] {total_emails}")
                # Display the first page without a spinner
            self.display_emails()
        except imaplib.IMAP4.error:
            self.console.print(f"[red]Authentication Error:[/red] Invalid credentials. Make sure you are using an App Password.")
        except Exception as e:
            self.console.print(f"[red]Error:[/red] {str(e)}")

    def display_emails(self):
        """Displays a page of 5 emails at a time without showing a loading spinner during navigation."""
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

            # Pagination controls
            self.console.print("\n[bold cyan]Commands:[/bold cyan] [blue]next[/blue] | [blue]prev[/blue] | [blue]select <number>[/blue] | [blue]exit[/blue]")
            if not self.pagination_controls(page_mail_ids):
                break

    def pagination_controls(self, page_mail_ids):
        """Handles pagination and selection of emails without a loading spinner."""
        while True:
            command = self.console.input("\nEnter command: ").strip().lower()

            if command == "next":
                if (self.page + 1) * self.page_size < len(self.mail_ids):
                    self.page += 1
                    self.display_emails()
                else:
                    self.console.print("[red]No more pages.[/red]")
            elif command == "prev":
                if self.page > 0:
                    self.page -= 1
                    self.display_emails()
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
                return False  # Exit pagination and return to main menu
            else:
                self.console.print("[red]Invalid command.[/red]")

    def display_email_detail(self, mail_id):
        """Displays the full details of a selected email."""
        with imaplib.IMAP4_SSL(self.imap_server) as mail:
            mail.login(self.username, self.password)
            mail.select('inbox')
            status, data = mail.fetch(mail_id, '(RFC822)')
            email_message = BytesParser().parsebytes(data[0][1])

            # Decode subject and sender with error handling for missing fields
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

    def send_mail(self, to, subject, message):
        """Sends an email with a loading animation."""
        self.setup_credentials()  # Ensure credentials are set up only once
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
            self.console.print("[red]Authentication Error:[/red] Invalid credentials or blocked access. Use an App Password for Gmail.")
        except Exception as e:
            self.console.print(f"[red]Error:[/red] {str(e)}")
