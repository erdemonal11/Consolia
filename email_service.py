import imaplib
import smtplib
import re
import json
import os
from email.mime.text import MIMEText
from email.parser import BytesParser
from email.header import decode_header
from rich.console import Console
from rich.panel import Panel
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
        self.favorites = []
        self.current_page_mail_ids = []
        self.signature = ""  

    def setup_credentials(self):
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
        self.setup_credentials()
        try:
            with imaplib.IMAP4_SSL(self.imap_server) as mail:
                mail.login(self.username, self.password)
                self.is_logged_in = True
                self.name = self.username.split("@")[0].title()
                self.console.print(f"[green]Hi, {self.name}! You are now logged in.[/green]")
                self.favorites_file = f"favorites_{self.username}.json"
                self.signature_file = f"signature_{self.username}.json"
                self.load_favorites()
                self.load_signature()  
        except imaplib.IMAP4.error:
            self.console.print("[red]Authentication Error:[/red] Invalid credentials. Make sure you are using an App Password.")
            self.username = self.password = None
            self.is_logged_in = False
        except Exception as e:
            self.console.print(f"[red]Error:[/red] {str(e)}")

    def logout(self):
        self.username = self.password = self.name = None
        self.is_logged_in = False
        self.favorites = []
        self.console.print("[green]You have successfully logged out.[/green]")

    def load_favorites(self):
        if os.path.exists(self.favorites_file):
            with open(self.favorites_file, "r") as file:
                self.favorites = json.load(file)
        else:
            self.favorites = []

    def save_favorites(self):
        with open(self.favorites_file, "w") as file:
            json.dump(self.favorites, file, indent=4)

    def load_signature(self):
        if os.path.exists(self.signature_file):
            with open(self.signature_file, "r") as file:
                self.signature = json.load(file).get("signature", "")
        else:
            self.signature = ""

    def save_signature(self):
        with open(self.signature_file, "w") as file:
            json.dump({"signature": self.signature}, file, indent=4)

    def set_signature(self):
        self.console.print("[bold yellow]Set Your Email Signature[/bold yellow]")
        self.signature = self.console.input("Enter your signature (or press Enter to leave blank): ")
        self.save_signature()
        self.console.print("[green]Signature saved successfully![/green]")

    def send_mail(self, to, subject, message):
        if not self.is_logged_in:
            self.console.print("[red]You need to log in first.[/red]")
            return

        include_signature = self.console.input("🖊️ [bold cyan]Do you want to include your signature? (y/n): [/bold cyan]").strip().lower()
        if include_signature == 'y' and self.signature:
            full_message = f"{message}\n\n{self.signature}"
        else:
            full_message = message

        try:
            msg = MIMEText(full_message)
            msg["Subject"] = subject
            msg["From"] = self.username
            msg["To"] = to

            with smtplib.SMTP_SSL(self.smtp_server, 465) as server:
                server.login(self.username, self.password)
                server.sendmail(self.username, to, msg.as_string())
            
            self.console.print("[green]Email sent successfully![/green]")
        except Exception as e:
            self.console.print(f"[red]Error sending email:[/red] {str(e)}")


    def fetch_mail_ids(self):
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
        while True:
            start = self.page * self.page_size
            end = start + self.page_size
            self.current_page_mail_ids = self.mail_ids[max(0, len(self.mail_ids) - end): len(self.mail_ids) - start]

            self.console.print("[bold cyan]Emails (page {}/{}):[/bold cyan]".format(self.page + 1, (len(self.mail_ids) // self.page_size) + 1))
            
            for i, mail_id in enumerate(self.current_page_mail_ids, start=1):
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

            self.console.print("\n[bold cyan]Commands:[/bold cyan] [blue]next[/blue] | [blue]prev[/blue] | [blue]go <page number>[/blue] | [blue]select <number>[/blue] | [blue]exit[/blue]")
            
            if not self.pagination_controls():
                break

    def pagination_controls(self):
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
            elif command.startswith("go "):
                try:
                    page_number = int(command.split(" ")[1]) - 1
                    if 0 <= page_number <= len(self.mail_ids) // self.page_size:
                        self.page = page_number
                        return True
                    else:
                        self.console.print("[red]Invalid page number.[/red]")
                except (IndexError, ValueError):
                    self.console.print("[red]Invalid command. Use 'go <page number>' to jump to a page.[/red]")
            elif command.startswith("select "):
                try:
                    index = int(command.split(" ")[1]) - 1
                    if 0 <= index < len(self.current_page_mail_ids):
                        self.display_email_detail(self.current_page_mail_ids[index])
                        return  
                    else:
                        self.console.print("[red]Invalid selection. Choose a number from the current page.[/red]")
                except (IndexError, ValueError):
                    self.console.print("[red]Invalid command. Use 'select <number>' to choose an email.[/red]")
            elif command == "exit":
                return False
            else:
                self.console.print("[red]Invalid command.[/red]")

    def display_email_detail(self, mail_id):
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

                def display_email_commands(is_favorited):
                    self.console.print(Panel(
                        f"[bold]From:[/bold] {from_address}\n[bold]Subject:[/bold] {subject}\n\n[bold]Message:[/bold]\n{body}",
                        title="📨 Full Email",
                        border_style="cyan",
                        box=box.ROUNDED
                    ))
                    command_options = "[blue]remove favorite[/blue]" if is_favorited else "[blue]favorite[/blue]"
                    self.console.print(f"\n[bold yellow]Commands:[/bold yellow] {command_options} | [blue]back[/blue]")

                is_favorited = any(fav["subject"] == subject for fav in self.favorites)
                display_email_commands(is_favorited)

                while True:
                    command = self.console.input("\nEnter command: ").strip().lower()

                    if command == "favorite" and not is_favorited:
                        self.add_to_favorites(subject, from_address, body)
                        is_favorited = True
                        display_email_commands(is_favorited)
                    elif command == "remove favorite" and is_favorited:
                        self.remove_from_favorites(subject)
                        is_favorited = False
                        display_email_commands(is_favorited)
                    elif command == "back":
                        return  
                    else:
                        self.console.print("[red]Invalid command. Please try again.[/red]")

        except Exception as e:
            self.console.print(f"[red]Error displaying email details: {e}[/red]")

    def add_to_favorites(self, subject, from_address, body):
        favorite_entry = {
            "subject": subject,
            "from": from_address,
            "body": body
        }
        self.favorites.append(favorite_entry)
        self.save_favorites()
        self.console.print("[green]Email added to favorites![/green]")

    def remove_from_favorites(self, subject):
        self.favorites = [entry for entry in self.favorites if entry["subject"] != subject]
        self.save_favorites()
        self.console.print("[green]Email removed from favorites![/green]")

    def display_favorites(self):
        page = 0
        page_size = 5
        while True:
            start = page * page_size
            end = start + page_size
            entries = self.favorites[start:end]
            self.console.print(f"[bold cyan]Favorite Emails (Page {page + 1}/{(len(self.favorites) - 1) // page_size + 1}):[/bold cyan]")
            
            for i, entry in enumerate(entries, start=1):
                self.console.print(Panel(
                    f"[bold]From:[/bold] {entry['from']}\n[bold]Subject:[/bold] {entry['subject']}",
                    title="⭐ Favorite Email",
                    border_style="green",
                    box=box.ROUNDED
                ))

            self.console.print("\n[bold yellow]Commands:[/bold yellow] [blue]next[/blue] | [blue]prev[/blue] | [blue]go <page number>[/blue] | [blue]read <number>[/blue] | [blue]remove <number>[/blue] | [blue]back[/blue]")
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
                    page_number = int(command.split(" ")[1]) - 1
                    if 0 <= page_number <= len(self.favorites) // page_size:
                        page = page_number
                    else:
                        self.console.print("[red]Invalid page number.[/red]")
                except (IndexError, ValueError):
                    self.console.print("[red]Invalid command. Use 'go <page number>' to jump to a page.[/red]")
            elif command.startswith("read "):
                try:
                    index = int(command.split(" ")[1]) - 1
                    if 0 <= index < len(entries):
                        self.display_full_favorite(entries[index])
                    else:
                        self.console.print("[red]Invalid selection. Please choose a valid number.[/red]")
                except (IndexError, ValueError):
                    self.console.print("[red]Invalid command. Use 'read <number>' to view an entry.[/red]")
            elif command.startswith("remove "):
                try:
                    index = int(command.split(" ")[1]) - 1
                    if 0 <= index < len(entries):
                        self.remove_from_favorites(entries[index]["subject"])
                        entries.pop(index)
                    else:
                        self.console.print("[red]Invalid selection. Please choose a valid number.[/red]")
                except (IndexError, ValueError):
                    self.console.print("[red]Invalid command. Use 'remove <number>' to delete an entry.[/red]")
            elif command == "back":
                return
            else:
                self.console.print("[red]Invalid command. Please try again.[/red]")

    def display_full_favorite(self, entry):
        while True:
            self.console.print(Panel(
                f"[bold]From:[/bold] {entry['from']}\n[bold]Subject:[/bold] {entry['subject']}\n\n[bold]Message:[/bold]\n{entry['body']}",
                title="⭐ Full Favorite Email",
                border_style="cyan",
                box=box.ROUNDED
            ))
            self.console.print("\n[bold yellow]Commands:[/bold yellow] [blue]remove favorite[/blue] | [blue]back[/blue]")

            command = self.console.input("\nEnter command: ").strip().lower()
            if command == "remove favorite":
                self.remove_from_favorites(entry["subject"])
                break  
            elif command == "back":
                break
            else:
                self.console.print("[red]Invalid command. Please try again.[/red]")

def main():
    email_service = EmailService()
    console = Console()
    
    while True:
        console.print("\n[bold yellow]🛠️   Options Menu:[/bold yellow]", style="bold underline")
        console.print("[bold green]1.[/bold green] 📧  Check Email")
        console.print("[bold green]2.[/bold green] ✉️   Send Email")
        console.print("[bold green]3.[/bold green] ⭐  Favorites")
        console.print("[bold green]4.[/bold green] 🖊️   Set Email Signature")  
        console.print("[bold green]5.[/bold green] 🔒  Logout")
        console.print("[bold green]=============================================[/bold green]")

        option = console.input("\nChoose an option: ").strip()

        if option == '1':
            email_service.fetch_mail_ids()
        elif option == '2':
            to = console.input("📬 [bold cyan]Recipient Email Address: [/bold cyan]")
            subject = console.input("📜 [bold cyan]Subject: [/bold cyan]")
            message = console.input("📝 [bold cyan]Message: [/bold cyan]")
            email_service.send_mail(to, subject, message)
        elif option == '3':
            email_service.display_favorites()
        elif option == '4':
            email_service.set_signature()  
        elif option == '5':
            email_service.logout()
            break
        else:
            console.print("[red]Invalid option. Please try again.[/red]")

