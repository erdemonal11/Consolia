import imaplib
import smtplib
from email.mime.text import MIMEText
from rich.console import Console

class EmailService:
    def __init__(self):
        self.console = Console()
        self.imap_server = 'imap.gmail.com'  # Update based on email provider
        self.smtp_server = 'smtp.gmail.com'
        self.username = 'your_email@example.com'
        self.password = 'your_password'
    
    def check_mail(self):
        self.console.print("[blue]Checking your emails...[/blue]")
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.username, self.password)
            mail.select('inbox')

            status, messages = mail.search(None, 'ALL')
            mail_ids = messages[0].split()

            for mail_id in mail_ids[:5]:  # Last 5 emails
                status, data = mail.fetch(mail_id, '(RFC822)')
                self.console.print(f"[green]Email ID:[/green] {mail_id.decode()}")
                self.console.print(data[0][1].decode())
        except Exception as e:
            self.console.print(f"[red]Error:[/red] {str(e)}")

    def send_mail(self, to, subject, message):
        self.console.print("[blue]Sending email...[/blue]")
        try:
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = self.username
            msg['To'] = to

            with smtplib.SMTP_SSL(self.smtp_server) as server:
                server.login(self.username, self.password)
                server.sendmail(self.username, to, msg.as_string())

            self.console.print("[green]Email sent successfully![/green]")
        except Exception as e:
            self.console.print(f"[red]Error:[/red] {str(e)}")
